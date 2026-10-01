from __future__ import annotations

from app.config.settings import Settings
from app.utils.errors import ConfigurationError, PublishInProgressError, SocialError
from app.utils.public_url import build_media_url

from .base import PublishResult, SocialPost
from .connections import ConnectionStore
from .factory import create_social_provider
from .pending import PendingPost, PendingPostStore


class SocialService:
    def __init__(self, settings: Settings, pending: PendingPostStore, connections: ConnectionStore) -> None:
        self.settings, self.pending, self.connections = settings, pending, connections

    async def register(self, chat_id: int, user_id: int, image: bytes, caption: str = "", hashtags: list[str] | None = None, platform: str = "") -> PendingPost:
        return await self.pending.create(chat_id, user_id, image, caption, hashtags, platform)

    async def select_platform(self, token: str, user_id: int, platform: str) -> PendingPost:
        post = self.pending.get(token)
        if not post or post.user_id != user_id:
            raise SocialError("preview missing or wrong owner")
        if platform not in {"instagram", "facebook", "linkedin", "x"}:
            raise SocialError("unsupported platform")
        post.platform = platform
        return post

    async def confirm(self, token: str, user_id: int) -> PublishResult:
        replay = self._published_result(token, user_id)
        if replay:
            return replay
        try:
            post = await self.pending.claim(token, user_id)
        except SocialError:
            replay = self._published_result(token, user_id)
            if replay:
                return replay
            existing = self.pending.get(token, include_terminal=True)
            if existing and existing.user_id == user_id and existing.status == "claimed":
                raise PublishInProgressError("publish already processing")
            raise
        credentials = self.connections.get(user_id, post.platform)
        provider = create_social_provider(post.platform, self.settings, credentials)
        if not provider:
            await self.pending.finish(token, False, {"reason": "unsupported platform"})
            raise SocialError("unsupported platform")
        status = await provider.get_status()
        if not status.configured:
            await self.pending.finish(token, False, {"reason": "not connected"})
            raise ConfigurationError("platform is not connected")
        try:
            media_url = build_media_url(self.settings.social_public_base_url, token) if post.platform in {"instagram", "facebook"} else ""
            payload = SocialPost(post.image_path, post.caption, post.hashtags, media_url)
            result = await provider.publish_post(payload)
        except Exception as exc:
            await self.pending.finish(token, False, {"reason": getattr(exc, "safe_message", "publish failed")})
            raise
        finally:
            await provider.close()
        await self.pending.finish(token, result.success, {"post_id": result.post_id, "permalink": result.permalink})
        return result

    def _published_result(self, token: str, user_id: int) -> PublishResult | None:
        post = self.pending.get(token, include_terminal=True)
        if not post or post.user_id != user_id or post.status != "published":
            return None
        return PublishResult(
            True,
            str(post.outcome.get("post_id", "")),
            str(post.outcome.get("permalink", "")),
            f"{post.platform.title()}-la already publish aayiduchu.",
        )
