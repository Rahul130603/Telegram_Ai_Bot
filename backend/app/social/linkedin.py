from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.utils.errors import AuthenticationError, SocialError
from app.utils.http import SafeHTTPClient

from .base import ProviderStatus, PublishResult, SocialMediaProvider, SocialPost


class LinkedInProvider(SocialMediaProvider):
    platform = "linkedin"

    def __init__(self, access_token: str, author_urn: str, client: httpx.AsyncClient | None = None) -> None:
        self.token, self.author = access_token, author_urn
        self.http = SafeHTTPClient(30, 1, client)
        self.version = datetime.now(timezone.utc).strftime("%Y%m")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "LinkedIn-Version": self.version, "X-Restli-Protocol-Version": "2.0.0"}

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus(bool(self.token and self.author), bool(self.token and self.author), self.author, "configured" if self.token and self.author else "token/author missing")

    async def authenticate(self) -> ProviderStatus:
        if not self.token or not self.author:
            raise AuthenticationError("LinkedIn configuration missing")
        return await self.get_status()

    async def publish_post(self, post: SocialPost) -> PublishResult:
        init = await self.http.request("POST", "https://api.linkedin.com/rest/images?action=initializeUpload", headers={**self.headers, "Content-Type": "application/json"}, json={"initializeUploadRequest": {"owner": self.author}})
        if init.status_code >= 400:
            raise SocialError(f"LinkedIn image registration failed ({init.status_code})")
        try:
            value = init.json()["value"]
            upload_url, image_urn = value["uploadUrl"], value["image"]
        except (KeyError, TypeError) as exc:
            raise SocialError("LinkedIn registration response malformed") from exc
        upload = await self.http.request("PUT", upload_url, side_effect=True, headers={"Authorization": f"Bearer {self.token}"}, content=post.image_path.read_bytes())
        if upload.status_code >= 400:
            raise SocialError(f"LinkedIn image upload failed ({upload.status_code})")
        payload = {"author": self.author, "commentary": post.text, "visibility": "PUBLIC", "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []}, "content": {"media": {"id": image_urn}}, "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
        response = await self.http.request("POST", "https://api.linkedin.com/rest/posts", side_effect=True, headers={**self.headers, "Content-Type": "application/json"}, json=payload)
        if response.status_code != 201:
            raise SocialError(f"LinkedIn post creation failed ({response.status_code})")
        post_id = response.headers.get("x-restli-id", "")
        return PublishResult(True, post_id, "", "LinkedIn-la publish aayiduchu.", {"image_urn": image_urn})

    async def close(self) -> None:
        await self.http.close()

