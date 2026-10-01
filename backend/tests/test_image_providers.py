import base64

import httpx
import pytest

from app.image.openai_images import OpenAIImageProvider


@pytest.mark.asyncio
async def test_openai_base64_image(png_bytes):
    async def handler(request):
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(png_bytes).decode()}]})
    provider = OpenAIImageProvider("k", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    image = await provider.generate("test")
    assert image.mime_type == "image/png" and image.data == png_bytes

