import httpx
import pytest

from app.ai.base import ChatMessage
from app.ai.openai_compatible import OpenAICompatibleProvider


@pytest.mark.asyncio
async def test_openai_compatible_payload():
    seen = {}
    async def handler(request):
        seen.update(__import__("json").loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    provider = OpenAICompatibleProvider("deepseek", "x", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    assert await provider.complete([ChatMessage("user", "hi")]) == "ok"
    assert seen["model"] == "deepseek-chat"

