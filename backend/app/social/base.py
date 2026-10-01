from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SocialPost:
    image_path: Path
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    media_url: str = ""

    @property
    def text(self) -> str:
        tags = " ".join(tag if tag.startswith("#") else f"#{tag}" for tag in self.hashtags)
        return "\n\n".join(part for part in (self.caption, tags) if part)


@dataclass
class PublishResult:
    success: bool
    post_id: str = ""
    permalink: str = ""
    safe_message: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ProviderStatus:
    configured: bool
    authenticated: bool = False
    account_name: str = ""
    safe_message: str = ""


class SocialMediaProvider(ABC):
    platform: str

    @abstractmethod
    async def get_status(self) -> ProviderStatus: ...

    @abstractmethod
    async def authenticate(self) -> ProviderStatus: ...

    async def create_post(self, post: SocialPost) -> object:
        return post

    @abstractmethod
    async def publish_post(self, post: SocialPost) -> PublishResult: ...

    async def close(self) -> None:
        return None

