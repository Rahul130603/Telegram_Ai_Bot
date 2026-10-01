from __future__ import annotations

import httpx

from app.utils.errors import AuthenticationError, NetworkError, SocialError
from app.utils.http import SafeHTTPClient
from app.utils.public_url import verify_public_media

from .base import ProviderStatus, PublishResult, SocialMediaProvider, SocialPost


class FacebookProvider(SocialMediaProvider):
    platform = "facebook"

    def __init__(self, access_token: str, page_id: str, graph_version: str = "v21.0", client: httpx.AsyncClient | None = None) -> None:
        self.token, self.page_id, self.version = access_token, page_id, graph_version
        self.http = SafeHTTPClient(30, 1, client)

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus(bool(self.token and self.page_id), False, safe_message="configured" if self.token and self.page_id else "Page token/ID missing")

    async def authenticate(self) -> ProviderStatus:
        response = await self.http.request("GET", f"https://graph.facebook.com/{self.version}/{self.page_id}", params={"fields": "id,name", "access_token": self.token})
        if response.status_code >= 400:
            raise AuthenticationError("Facebook Page authentication failed")
        return ProviderStatus(True, True, response.json().get("name", ""), "connected")

    async def publish_post(self, post: SocialPost) -> PublishResult:
        if not post.media_url:
            raise SocialError("Facebook requires a public media URL")
        try:
            await verify_public_media(post.media_url, self.http.client)
        except Exception as exc:
            raise NetworkError("Facebook image URL unreachable") from exc
        response = await self.http.request("POST", f"https://graph.facebook.com/{self.version}/{self.page_id}/photos", side_effect=True, data={"url": post.media_url, "caption": post.text, "published": "true", "access_token": self.token})
        if response.status_code >= 400:
            raise SocialError(f"Facebook photo publication failed ({response.status_code})")
        body = response.json()
        post_id = str(body.get("post_id") or body.get("id") or "")
        return PublishResult(True, post_id, f"https://www.facebook.com/{post_id}" if post_id else "", "Facebook Page-la publish aayiduchu.")

    async def close(self) -> None:
        await self.http.close()

