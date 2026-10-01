from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.utils.errors import ExpiredError, OwnershipError, SocialError
from app.utils.imaging import validate_image

Status = Literal["pending", "claimed", "published", "failed", "cancelled"]


@dataclass
class PendingPost:
    token: str
    chat_id: int
    user_id: int
    image_path: Path
    mime_type: str
    caption: str
    hashtags: list[str]
    platform: str
    created_at: float
    expires_at: float
    status: Status = "pending"
    preview_message_id: int | None = None
    outcome: dict[str, object] = field(default_factory=dict)

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


class PendingPostStore:
    def __init__(self, directory: Path, ttl_seconds: int = 1800, max_per_chat: int = 5) -> None:
        self.directory = directory
        self.ttl = ttl_seconds
        self.max_per_chat = max_per_chat
        self._items: dict[str, PendingPost] = {}
        self._lock = asyncio.Lock()
        directory.mkdir(parents=True, exist_ok=True)

    async def create(self, chat_id: int, user_id: int, image_bytes: bytes, caption: str = "", hashtags: list[str] | None = None, platform: str = "") -> PendingPost:
        mime, _ = validate_image(image_bytes)
        async with self._lock:
            self.cleanup()
            active = [post for post in self._items.values() if post.chat_id == chat_id and post.status == "pending"]
            if len(active) >= self.max_per_chat:
                oldest = min(active, key=lambda item: item.created_at)
                oldest.status = "cancelled"
            token = secrets.token_urlsafe(24)
            suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[mime]
            path = self.directory / f"{secrets.token_hex(16)}{suffix}"
            path.write_bytes(image_bytes)
            now = time.time()
            post = PendingPost(token, chat_id, user_id, path, mime, caption, hashtags or [], platform, now, now + self.ttl)
            self._items[token] = post
            return post

    def get(self, token: str, *, include_terminal: bool = False) -> PendingPost | None:
        post = self._items.get(token)
        if not post or post.expired or not post.image_path.is_file():
            return None
        if not include_terminal and post.status != "pending":
            return None
        return post

    async def claim(self, token: str, user_id: int) -> PendingPost:
        async with self._lock:
            post = self._items.get(token)
            if not post or post.expired:
                raise ExpiredError("preview expired")
            if post.user_id != user_id:
                raise OwnershipError("wrong preview owner")
            if post.status != "pending":
                raise SocialError(f"preview already {post.status}")
            post.status = "claimed"
            return post

    async def cancel(self, token: str, user_id: int) -> PendingPost:
        async with self._lock:
            post = self._items.get(token)
            if not post or post.expired:
                raise ExpiredError("preview expired")
            if post.user_id != user_id:
                raise OwnershipError("wrong preview owner")
            if post.status != "pending":
                raise SocialError("preview is not cancellable")
            post.status = "cancelled"
            return post

    async def finish(self, token: str, success: bool, outcome: dict[str, object]) -> None:
        async with self._lock:
            post = self._items[token]
            post.status = "published" if success else "failed"
            post.outcome = outcome

    def cleanup(self) -> int:
        removed = 0
        for token, post in list(self._items.items()):
            if post.expired:
                self._items.pop(token, None)
                post.image_path.unlink(missing_ok=True)
                removed += 1
        return removed

