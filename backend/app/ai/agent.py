from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.config.prompts import ASSISTANT_PROMPT, IMAGE_SPEC_PROMPT, ROUTER_PROMPT
from app.utils.text import extract_json

from .base import ChatMessage, LLMProvider
from .memory import ConversationMemory

Intent = Literal["chat", "content", "image"]


@dataclass
class ImageSpec:
    visual_prompt: str
    overlay_lines: list[str] = field(default_factory=list)
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    no_text: bool = False


@dataclass
class AgentResponse:
    intent: Intent
    text: str = ""
    image_spec: ImageSpec | None = None


IMAGE_WORDS = re.compile(r"\b(image|photo|picture|poster|banner|flyer|visual|logo|thumbnail|advertisement|ad creative|படம்|போஸ்டர்)\b", re.I)
CREATE_WORDS = re.compile(r"\b(create|generate|make|draw|design|உருவாக்கு|பண்ணு|venum|வேண்டும்)\b", re.I)
CONTENT_WORDS = re.compile(r"\b(caption|hashtags?|post copy|content|bio|script|write|எழுது)\b", re.I)
NO_TEXT = re.compile(r"\b(no text|without text|text[- ]free|எழுத்து வேண்டாம்)\b", re.I)


class AIAgent:
    def __init__(self, llm: LLMProvider, memory: ConversationMemory | None = None, max_input_chars: int = 4000) -> None:
        self.llm = llm
        self.memory = memory or ConversationMemory()
        self.max_input_chars = max_input_chars

    async def classify(self, text: str) -> Intent:
        if CONTENT_WORDS.search(text) and not IMAGE_WORDS.search(text):
            return "content"
        if IMAGE_WORDS.search(text) and CREATE_WORDS.search(text):
            return "image"
        if not self.llm.configured:
            return "chat"
        reply = await self.llm.complete([ChatMessage("system", ROUTER_PROMPT), ChatMessage("user", text)], json_mode=True)
        try:
            intent = extract_json(reply).get("intent", "chat")
        except ValueError:
            return "chat"
        return intent if intent in {"chat", "content", "image"} else "chat"

    async def image_spec(self, text: str) -> ImageSpec:
        no_text = bool(NO_TEXT.search(text))
        if self.llm.configured:
            try:
                reply = await self.llm.complete([ChatMessage("system", IMAGE_SPEC_PROMPT), ChatMessage("user", text)], json_mode=True)
                data = extract_json(reply)
                lines = [] if no_text else [str(line) for line in data.get("overlay_lines", [])][:4]
                return ImageSpec(str(data.get("visual_prompt") or text), lines, str(data.get("caption", "")), [str(v) for v in data.get("hashtags", [])], no_text)
            except Exception:
                pass
        cleaned = NO_TEXT.sub("", text).strip()
        prompt = f"Professional social media artwork, clear focal subject, balanced composition: {cleaned}"
        return ImageSpec(prompt, no_text=no_text)

    async def handle(self, chat_id: int, text: str) -> AgentResponse:
        text = text.strip()
        if not text:
            return AgentResponse("chat", "Message empty-a irukku.")
        if len(text) > self.max_input_chars:
            return AgentResponse("chat", f"Message romba long. {self.max_input_chars} characters-kulla anuppunga.")
        intent = await self.classify(text)
        if intent == "image":
            return AgentResponse("image", image_spec=await self.image_spec(text))
        messages = [ChatMessage("system", ASSISTANT_PROMPT), *self.memory.get(chat_id), ChatMessage("user", text)]
        reply = await self.llm.complete(messages)
        self.memory.add(chat_id, "user", text)
        self.memory.add(chat_id, "assistant", reply)
        return AgentResponse(intent, reply)

