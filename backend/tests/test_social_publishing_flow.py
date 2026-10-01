import pytest

from app.config.settings import Settings
from app.social.connections import ConnectionStore
from app.social.pending import PendingPostStore
from app.social.service import SocialService


@pytest.mark.asyncio
async def test_registration_never_publishes(tmp_path, png_bytes):
    settings = Settings(_env_file=None, social_pending_dir=str(tmp_path), social_enabled=True)
    service = SocialService(settings, PendingPostStore(tmp_path), ConnectionStore(tmp_path / "db"))
    post = await service.register(1, 2, png_bytes)
    assert post.status == "pending" and post.outcome == {}


@pytest.mark.asyncio
async def test_repeated_confirm_returns_original_publish_success(tmp_path, png_bytes):
    settings = Settings(_env_file=None, social_pending_dir=str(tmp_path), social_enabled=True)
    pending = PendingPostStore(tmp_path)
    service = SocialService(settings, pending, ConnectionStore(tmp_path / "db"))
    post = await service.register(1, 2, png_bytes, platform="instagram")
    await pending.claim(post.token, 2)
    await pending.finish(post.token, True, {"post_id": "123", "permalink": "https://example.com/post/123"})

    result = await service.confirm(post.token, 2)

    assert result.success is True
    assert result.post_id == "123"
    assert result.permalink == "https://example.com/post/123"
    assert "already publish" in result.safe_message
