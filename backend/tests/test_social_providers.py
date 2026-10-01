import httpx
import pytest

from app.social.base import SocialPost
from app.social.facebook import FacebookProvider


@pytest.mark.asyncio
async def test_facebook_photo_payload(monkeypatch, tmp_path, jpeg_bytes):
    seen = {}
    async def handler(request):
        if request.method == "GET":
            return httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
        seen.update(dict(request.url.params) if request.url.params else dict(__import__("urllib.parse").parse.parse_qsl(request.content.decode())))
        return httpx.Response(200, json={"post_id": "1_2"})
    monkeypatch.setattr("app.social.facebook.verify_public_media", lambda *args, **kwargs: __import__("asyncio").sleep(0))
    path = tmp_path / "x.jpg"
    path.write_bytes(jpeg_bytes)
    provider = FacebookProvider("t", "p", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    result = await provider.publish_post(SocialPost(path, "caption", media_url="https://example.com/media/pending/x"))
    assert result.success and seen["published"] == "true" and seen["url"].endswith("/x")

