from __future__ import annotations

import httpx

from app.utils.errors import AuthenticationError, SocialError
from app.utils.http import SafeHTTPClient

from .base import ProviderStatus, PublishResult, SocialMediaProvider, SocialPost
from .oauth1 import oauth1_authorization


class XProvider(SocialMediaProvider):
    platform = "x"

    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str, oauth2_token: str = "", client: httpx.AsyncClient | None = None) -> None:
        self.api_key, self.api_secret = api_key, api_secret
        self.access_token, self.access_secret, self.oauth2_token = access_token, access_secret, oauth2_token
        self.http = SafeHTTPClient(30, 0, client)

    async def get_status(self) -> ProviderStatus:
        configured = bool(self.oauth2_token or (self.api_key and self.api_secret and self.access_token and self.access_secret))
        return ProviderStatus(configured, configured, safe_message="configured" if configured else "X credentials missing")

    async def authenticate(self) -> ProviderStatus:
        status = await self.get_status()
        if not status.configured:
            raise AuthenticationError("X credentials missing")
        return status

    async def publish_post(self, post: SocialPost) -> PublishResult:
        if self.oauth2_token:
            raise SocialError("OAuth 2 connection cannot upload media for this X API configuration; connect OAuth 1.0a credentials")
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        auth = oauth1_authorization("POST", upload_url, {}, self.api_key, self.api_secret, self.access_token, self.access_secret)
        upload = await self.http.request("POST", upload_url, side_effect=True, headers={"Authorization": auth}, files={"media": (post.image_path.name, post.image_path.read_bytes(), "application/octet-stream")})
        if upload.status_code >= 400:
            raise SocialError(f"X media upload failed ({upload.status_code})")
        media_id = str(upload.json().get("media_id_string", ""))
        if not media_id:
            raise SocialError("X media upload returned no ID")
        tweet_url = "https://api.twitter.com/2/tweets"
        auth = oauth1_authorization("POST", tweet_url, {}, self.api_key, self.api_secret, self.access_token, self.access_secret)
        response = await self.http.request("POST", tweet_url, side_effect=True, headers={"Authorization": auth, "Content-Type": "application/json"}, json={"text": post.text, "media": {"media_ids": [media_id]}})
        if response.status_code >= 400:
            raise SocialError(f"X post creation failed ({response.status_code})")
        post_id = str(response.json().get("data", {}).get("id", ""))
        return PublishResult(True, post_id, f"https://x.com/i/web/status/{post_id}" if post_id else "", "X-la publish aayiduchu.")

    async def close(self) -> None:
        await self.http.close()

