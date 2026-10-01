from __future__ import annotations

import time
from collections import defaultdict, deque

from .base import ChatMessage


class ConversationMemory:
    def __init__(self, turns: int = 8, ttl_seconds: int = 3600) -> None:
        self.turns = turns
        self.ttl = ttl_seconds
        self._items: dict[int, deque[tuple[float, ChatMessage]]] = defaultdict(lambda: deque(maxlen=turns * 2))

    def get(self, chat_id: int) -> list[ChatMessage]:
        now = time.monotonic()
        items = self._items[chat_id]
        while items and items[0][0] <= now - self.ttl:
            items.popleft()
        return [message for _, message in items]

    def add(self, chat_id: int, role: str, content: str) -> None:
        self.get(chat_id)
        self._items[chat_id].append((time.monotonic(), ChatMessage(role, content)))

    def clear(self, chat_id: int) -> None:
        self._items.pop(chat_id, None)

