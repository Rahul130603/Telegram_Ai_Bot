from __future__ import annotations

import asyncio

from app.ai.agent import AIAgent
from app.ai.base import ChatMessage, LLMProvider


class MockLLM(LLMProvider):
    configured = True

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        return '{"intent":"content"}' if json_mode else "Mocked answer — no external API called."


async def main() -> int:
    agent = AIAgent(MockLLM())
    chat = await agent.handle(1, "Hello")
    image = await agent.handle(1, "Create an image of sunrise without text")
    ok = chat.text.startswith("Mocked") and image.intent == "image" and image.image_spec.no_text
    print({"offline_smoke_ok": ok, "live_publish_attempted": False})
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

