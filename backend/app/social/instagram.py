from __future__ import annotations

import asyncio

import httpx

from app.utils.errors import AuthenticationError, NetworkError, SocialError
from app.utils.http import SafeHTTPClient
from app.utils.public_url import verify_public_media

from .base import ProviderStatus, PublishResult, SocialMediaProvider, SocialPost


class InstagramProvider(SocialMediaProvider):
    platform = "instagram"

    def __init__(self, access_token: str, account_id: str, flow: str = "facebook", graph_version: str = "v21.0", client: httpx.AsyncClient | None = None) -> None:
        self.token, self.account_id, self.flow, self.version = access_token, account_id, flow, graph_version
        self.host = "https://graph.instagram.com" if flow == "instagram" else "https://graph.facebook.com"
        self.http = SafeHTTPClient(30, 1, client)

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus(bool(self.token and self.account_id), False, safe_message="configured" if self.token and self.account_id else "token/account missing")

    async def authenticate(self) -> ProviderStatus:
        if not self.token or not self.account_id:
            return await self.get_status()
        response = await self.http.request("GET", f"{self.host}/{self.version}/{self.account_id}", params={"fields": "id,username,name", "access_token": self.token})
        if response.status_code >= 400:
            raise AuthenticationError("Instagram account authentication failed")
        body = response.json()
        return ProviderStatus(True, True, body.get("username") or body.get("name", ""), "connected")

    async def publish_post(self, post: SocialPost) -> PublishResult:
        if not post.media_url:
            raise SocialError("Instagram requires a public media URL")
        try:
            await verify_public_media(post.media_url, self.http.client)
        except Exception as exc:
            raise NetworkError("Instagram image URL unreachable") from exc
        create = await self.http.request("POST", f"{self.host}/{self.version}/{self.account_id}/media", side_effect=True, data={"image_url": post.media_url, "caption": post.text, "access_token": self.token})
        if create.status_code >= 400:
            raise SocialError(f"Instagram container creation failed ({create.status_code})")
        container_id = create.json().get("id")
        if not container_id:
            raise SocialError("Instagram container ID missing")
        for _ in range(10):
            status = await self.http.request("GET", f"{self.host}/{self.version}/{container_id}", params={"fields": "status_code,status", "access_token": self.token})
            if status.status_code >= 400:
                raise SocialError(f"Instagram container status failed ({status.status_code})")
            code = status.json().get("status_code")
            if code == "FINISHED":
                break
            if code in {"ERROR", "EXPIRED"}:
                raise SocialError(f"Instagram container {code.lower()}")
            await asyncio.sleep(1)
        else:
            raise SocialError("Instagram container processing timed out")
        publish = await self.http.request("POST", f"{self.host}/{self.version}/{self.account_id}/media_publish", side_effect=True, data={"creation_id": container_id, "access_token": self.token})
        if publish.status_code >= 400:
            raise SocialError(f"Instagram final publication failed ({publish.status_code})")
        post_id = str(publish.json().get("id", ""))
        permalink = ""
        if post_id:
            details = await self.http.request("GET", f"{self.host}/{self.version}/{post_id}", params={"fields": "permalink", "access_token": self.token})
            if details.status_code < 400:
                permalink = details.json().get("permalink", "")
        return PublishResult(True, post_id, permalink, "Instagram-la publish aayiduchu.", {"container_id": container_id})

    async def close(self) -> None:
        await self.http.close()

