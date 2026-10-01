from __future__ import annotations

import base64

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class ImagenProvider(ImageProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key, self.model = api_key, model
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        if not self.configured:
            raise ConfigurationError("Imagen API configuration missing")
        response = await self.http.request("POST", f"{self.base_url}/models/{self.model}:predict", headers={"x-goog-api-key": self.api_key}, json={"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}})
        if response.status_code >= 400:
            raise safe_status_error(response, "Imagen generation")
        try:
            value = response.json()["predictions"][0]
            data = base64.b64decode(value.get("bytesBase64Encoded") or value["bytes_base64_encoded"], validate=True)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("Imagen returned no valid image") from exc
        return GeneratedImage(data, metadata={"provider": "imagen", "model": self.model})

    async def close(self) -> None:
        await self.http.close()

