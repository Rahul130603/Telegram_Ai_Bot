import pytest

from app.ai.agent import AIAgent
from app.ai.factory import DisabledLLM


@pytest.mark.asyncio
async def test_multilingual_image_intent_and_no_text_fallback():
    agent = AIAgent(DisabledLLM())
    result = await agent.handle(1, "Create poster படம் without text")
    assert result.intent == "image"
    assert result.image_spec.no_text and result.image_spec.overlay_lines == []

