from __future__ import annotations

import base64

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import GeneratedImage, ImageProvider


class CloudflareImageProvider(ImageProvider):
    def __init__(self, token: str, account_id: str, model: str = "@cf/black-forest-labs/flux-1-schnell", timeout: float = 120, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.token, self.account_id = token, account_id
        self.model = model or "@cf/black-forest-labs/flux-1-schnell"
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.token and self.account_id)

    async def generate(self, prompt: str, size: str = "1024x1024") -> GeneratedImage:
        if not self.configured:
            raise ConfigurationError("Cloudflare token/account missing")
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        # FLUX.1 Schnell's Workers AI schema accepts prompt and optional steps.
        # It does not accept generic width/height fields; sending them produces HTTP 400.
        response = await self.http.request(
            "POST",
            url,
            headers={"Authorization": f"Bearer {self.token}"},
            json={"prompt": prompt, "steps": 4},
        )
        if response.status_code >= 400:
            raise safe_status_error(response, "Cloudflare image generation")
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("image/"):
            data = response.content
        else:
            try:
                body = response.json()
                if body.get("success") is False:
                    raise ProviderError("Cloudflare reported generation failure")
                result = body.get("result", body)
                encoded = result.get("image") or result.get("b64_json") or result.get("base64")
                data = base64.b64decode(encoded, validate=True)
            except (AttributeError, TypeError, ValueError) as exc:
                raise ProviderError("malformed Cloudflare image response") from exc
        return GeneratedImage(
            data,
            metadata={"provider": "cloudflare", "model": self.model, "requested_size": size},
        )

    async def close(self) -> None:
        await self.http.close()

