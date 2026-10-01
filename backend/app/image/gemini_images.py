from __future__ import annotations

import base64

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class GeminiImageProvider(ImageProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-preview-image-generation", base_url: str = "https://generativelanguage.googleapis.com/v1beta", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash-preview-image-generation"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        if not self.configured:
            raise ConfigurationError("Gemini image API key missing")
        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
        response = await self.http.request("POST", url, headers={"x-goog-api-key": self.api_key}, json=payload)
        if response.status_code >= 400:
            raise safe_status_error(response, "Gemini image generation")
        try:
            parts = response.json()["candidates"][0]["content"]["parts"]
            part = next(item for item in parts if item.get("inlineData") or item.get("inline_data"))
            inline = part.get("inlineData") or part["inline_data"]
            data = base64.b64decode(inline["data"], validate=True)
        except (KeyError, IndexError, StopIteration, TypeError, ValueError) as exc:
            raise ProviderError("Gemini returned no valid image") from exc
        return GeneratedImage(data, metadata={"provider": "gemini", "model": self.model})

    async def close(self) -> None:
        await self.http.close()

