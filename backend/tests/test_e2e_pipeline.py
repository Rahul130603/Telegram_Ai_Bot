import pytest

from app.ai.agent import AIAgent
from app.ai.factory import DisabledLLM
from app.config.settings import Settings
from app.social.connections import ConnectionStore
from app.social.pending import PendingPostStore
from app.social.service import SocialService


@pytest.mark.asyncio
async def test_mocked_request_to_preview_without_publish(tmp_path, png_bytes):
    agent = AIAgent(DisabledLLM())
    result = await agent.handle(10, "Create an image of a tea shop poster without text")
    assert result.intent == "image"
    settings = Settings(_env_file=None, social_pending_dir=str(tmp_path))
    pending = PendingPostStore(tmp_path)
    service = SocialService(settings, pending, ConnectionStore(tmp_path / "db"))
    preview = await service.register(10, 20, png_bytes, result.image_spec.caption, result.image_spec.hashtags)
    await service.select_platform(preview.token, 20, "instagram")
    assert preview.status == "pending" and preview.outcome == {}

