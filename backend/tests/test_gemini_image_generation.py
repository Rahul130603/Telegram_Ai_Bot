import base64

import httpx
import pytest

from app.image.gemini_images import GeminiImageProvider
from app.image.imagen import ImagenProvider


@pytest.mark.asyncio
async def test_gemini_and_imagen_use_distinct_endpoints(png_bytes):
    paths = []
    async def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith(":predict"):
            return httpx.Response(200, json={"predictions": [{"bytesBase64Encoded": base64.b64encode(png_bytes).decode()}]})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"inlineData": {"data": base64.b64encode(png_bytes).decode()}}]}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await GeminiImageProvider("k", client=client).generate("x")
    await ImagenProvider("k", "imagen-3", client=client).generate("x")
    assert paths[0].endswith(":generateContent") and paths[1].endswith(":predict")

