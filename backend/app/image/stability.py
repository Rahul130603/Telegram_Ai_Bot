from __future__ import annotations

import httpx

from app.utils.errors import ConfigurationError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class StabilityImageProvider(ImageProvider):
    def __init__(self, api_key: str, model: str = "stable-image-core", base_url: str = "https://api.stability.ai/v2beta", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key, self.model = api_key, model or "stable-image-core"
        self.base_url = (base_url or "https://api.stability.ai/v2beta").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        if not self.configured:
            raise ConfigurationError("Stability API key missing")
        endpoint = f"{self.base_url}/stable-image/generate/{self.model}"
        response = await self.http.request("POST", endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Accept": "image/*"}, files={"prompt": (None, prompt), "output_format": (None, "png")})
        if response.status_code >= 400:
            raise safe_status_error(response, "Stability generation")
        return GeneratedImage(response.content, metadata={"provider": "stability"})

    async def close(self) -> None:
        await self.http.close()

