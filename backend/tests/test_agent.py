import pytest

from app.ai.agent import AIAgent
from app.ai.base import LLMProvider


class FakeLLM(LLMProvider):
    configured = True
    async def complete(self, messages, *, json_mode=False):
        return '{"intent":"chat"}' if json_mode else "reply"


@pytest.mark.asyncio
async def test_content_not_image_and_memory():
    agent = AIAgent(FakeLLM())
    result = await agent.handle(1, "Write an Instagram caption")
    assert result.intent == "content" and result.text == "reply"
    assert len(agent.memory.get(1)) == 2 and not agent.memory.get(2)

