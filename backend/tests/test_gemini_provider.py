import httpx
import pytest

from app.ai.base import ChatMessage
from app.ai.gemini import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_parses_text():
    async def handler(request):
        assert request.headers["x-goog-api-key"] == "k"
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "vanakkam"}]}}]})
    provider = GeminiProvider("k", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    assert await provider.complete([ChatMessage("user", "hi")]) == "vanakkam"

