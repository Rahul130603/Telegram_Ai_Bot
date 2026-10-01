from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LLMProvider(ABC):
    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str: ...

    async def close(self) -> None:
        return None

