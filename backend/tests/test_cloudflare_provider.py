import base64

import httpx
import pytest

from app.image.cloudflare import CloudflareImageProvider


@pytest.mark.asyncio
async def test_cloudflare_envelope(png_bytes):
    async def handler(request):
        assert "/accounts/account/ai/run/" in str(request.url)
        assert request.content == b'{"prompt":"x","steps":4}'
        return httpx.Response(200, json={"success": True, "result": {"image": base64.b64encode(png_bytes).decode()}})
    provider = CloudflareImageProvider("token", "account", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    assert (await provider.generate("x")).mime_type == "image/png"

