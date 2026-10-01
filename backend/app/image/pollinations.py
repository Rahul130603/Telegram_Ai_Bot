from __future__ import annotations

from urllib.parse import quote

import httpx

from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class PollinationsProvider(ImageProvider):
    def __init__(self, api_key: str = "", model: str = "", base_url: str = "https://image.pollinations.ai", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://image.pollinations.ai").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return True

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        width, height = size.split("x")
        params: dict[str, str] = {"width": width, "height": height, "nologo": "true"}
        if self.model:
            params["model"] = self.model
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = await self.http.request("GET", f"{self.base_url}/prompt/{quote(prompt, safe='')}", params=params, headers=headers)
        if response.status_code >= 400:
            raise safe_status_error(response, "Pollinations generation")
        return GeneratedImage(response.content, metadata={"provider": "pollinations"})

    async def close(self) -> None:
        await self.http.close()

