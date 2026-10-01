from __future__ import annotations

import base64

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class OpenAIImageProvider(ImageProvider):
    def __init__(self, api_key: str, model: str = "gpt-image-1", base_url: str = "https://api.openai.com/v1", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.model = model or "gpt-image-1"
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        if not self.configured:
            raise ConfigurationError("OpenAI image API key missing")
        response = await self.http.request("POST", f"{self.base_url}/images/generations", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "prompt": prompt, "size": size, "response_format": "b64_json"})
        if response.status_code >= 400:
            raise safe_status_error(response, "OpenAI image generation")
        try:
            item = response.json()["data"][0]
            if item.get("b64_json"):
                data = base64.b64decode(item["b64_json"], validate=True)
            elif item.get("url"):
                fetched = await self.http.request("GET", item["url"])
                if fetched.status_code >= 400:
                    raise safe_status_error(fetched, "OpenAI image download")
                data = fetched.content
            else:
                raise ProviderError("OpenAI returned no image")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("malformed OpenAI image response") from exc
        return GeneratedImage(data, metadata={"provider": "openai", "model": self.model})

    async def close(self) -> None:
        await self.http.close()

