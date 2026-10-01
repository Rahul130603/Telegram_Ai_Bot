from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config.settings import Settings
from app.utils.errors import AuthenticationError, ConfigurationError
from app.utils.http import SafeHTTPClient
from app.utils.public_url import normalize_public_base_url

from .connections import ConnectionStore
from .credentials import SocialCredentials


@dataclass
class OAuthState:
    value: str
    platform: str
    user_id: int
    expires_at: float
    redirect_uri: str
    verifier: str = ""


class OAuthStateStore:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl = ttl_seconds
        self._states: dict[str, OAuthState] = {}

    def create(self, platform: str, user_id: int, redirect_uri: str, verifier: str = "") -> OAuthState:
        state = OAuthState(secrets.token_urlsafe(32), platform, user_id, time.time() + self.ttl, redirect_uri, verifier)
        self._states[state.value] = state
        return state

    def consume(self, value: str, platform: str) -> OAuthState:
        state = self._states.pop(value, None)
        if not state or state.platform != platform or state.expires_at <= time.time():
            raise AuthenticationError("invalid, expired, or replayed OAuth state")
        return state


class OAuthManager:
    def __init__(self, settings: Settings, connections: ConnectionStore, states: OAuthStateStore | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.settings, self.connections = settings, connections
        self.states = states or OAuthStateStore(settings.oauth_state_ttl_seconds)
        self.http = SafeHTTPClient(30, 1, client)

    def redirect_uri(self, platform: str) -> str:
        return f"{normalize_public_base_url(self.settings.social_public_base_url)}/auth/{platform}/callback"

    def consent_url(self, platform: str, user_id: int) -> str:
        redirect = self.redirect_uri(platform)
        verifier = secrets.token_urlsafe(48) if platform == "x" else ""
        state = self.states.create(platform, user_id, redirect, verifier)
        if platform == "facebook":
            if not self.settings.facebook_app_id:
                raise ConfigurationError("FACEBOOK_APP_ID missing")
            params = {
                "client_id": self.settings.facebook_app_id,
                "redirect_uri": redirect,
                "state": state.value,
                # Facebook Page publishing only. Instagram uses its own
                # configured login/token flow and must not block this consent.
                "scope": "pages_show_list,pages_read_engagement,pages_manage_posts",
                "response_type": "code",
            }
            return "https://www.facebook.com/dialog/oauth?" + urlencode(params)
        if platform == "linkedin":
            if not self.settings.linkedin_client_id:
                raise ConfigurationError("LINKEDIN_CLIENT_ID missing")
            params = {"client_id": self.settings.linkedin_client_id, "redirect_uri": redirect, "state": state.value, "scope": "openid profile w_member_social", "response_type": "code"}
            return "https://www.linkedin.com/oauth/v2/authorization?" + urlencode(params)
        if platform == "x":
            if not self.settings.x_client_id:
                raise ConfigurationError("X_CLIENT_ID missing")
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
            params = {"client_id": self.settings.x_client_id, "redirect_uri": redirect, "state": state.value, "scope": "tweet.read tweet.write users.read offline.access", "response_type": "code", "code_challenge": challenge, "code_challenge_method": "S256"}
            return "https://twitter.com/i/oauth2/authorize?" + urlencode(params)
        raise ConfigurationError("unsupported OAuth platform")

    async def callback(self, platform: str, code: str, state_value: str) -> SocialCredentials:
        state = self.states.consume(state_value, platform)
        if platform == "facebook":
            token_url = "https://graph.facebook.com/v21.0/oauth/access_token"
            data = {"client_id": self.settings.facebook_app_id, "client_secret": self.settings.facebook_app_secret.get_secret_value(), "redirect_uri": state.redirect_uri, "code": code}
        elif platform == "linkedin":
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {"grant_type": "authorization_code", "client_id": self.settings.linkedin_client_id, "client_secret": self.settings.linkedin_client_secret.get_secret_value(), "redirect_uri": state.redirect_uri, "code": code}
        elif platform == "x":
            token_url = "https://api.twitter.com/2/oauth2/token"
            data = {"grant_type": "authorization_code", "client_id": self.settings.x_client_id, "redirect_uri": state.redirect_uri, "code": code, "code_verifier": state.verifier}
        else:
            raise AuthenticationError("unsupported OAuth callback")
        response = await self.http.request("POST", token_url, data=data)
        if response.status_code >= 400:
            raise AuthenticationError(f"{platform} token exchange failed")
        body = response.json()
        token = body.get("access_token", "")
        if not token:
            raise AuthenticationError("OAuth token missing")
        if platform == "facebook":
            pages = await self.http.request("GET", "https://graph.facebook.com/v21.0/me/accounts", params={"fields": "id,name,access_token,instagram_business_account", "access_token": token})
            if pages.status_code >= 400 or not pages.json().get("data"):
                raise AuthenticationError("No managed Facebook Pages found")
            page = pages.json()["data"][0]
            credentials = SocialCredentials("facebook", page.get("access_token", token), str(page["id"]), page.get("name", ""), "page")
        elif platform == "linkedin":
            info = await self.http.request("GET", "https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {token}"})
            if info.status_code >= 400:
                raise AuthenticationError("LinkedIn account discovery failed")
            profile = info.json()
            credentials = SocialCredentials("linkedin", token, f"urn:li:person:{profile['sub']}", profile.get("name", ""), "member", refresh_token=body.get("refresh_token", ""), scope=body.get("scope", ""))
        else:
            info = await self.http.request("GET", "https://api.twitter.com/2/users/me", headers={"Authorization": f"Bearer {token}"})
            if info.status_code >= 400:
                raise AuthenticationError("X account discovery failed")
            profile = info.json().get("data", {})
            credentials = SocialCredentials("x", token, str(profile.get("id", "")), profile.get("name", ""), "user", refresh_token=body.get("refresh_token", ""), scope=body.get("scope", ""))
        self.connections.set(state.user_id, credentials)
        return credentials

    async def close(self) -> None:
        await self.http.close()

