from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.social.media import create_media_router
from app.social.pending import PendingPostStore


def test_public_media_jpeg_and_png_conversion(tmp_path, jpeg_bytes, png_bytes):
    import asyncio
    store = PendingPostStore(tmp_path)
    jpeg = asyncio.run(store.create(1, 1, jpeg_bytes))
    png = asyncio.run(store.create(1, 1, png_bytes))
    app = FastAPI()
    app.include_router(create_media_router(store))
    client = TestClient(app)
    first = client.get(f"/media/pending/{jpeg.token}")
    second = client.get(f"/media/pending/{png.token}")
    assert first.content == jpeg_bytes and first.headers["content-type"] == "image/jpeg"
    assert second.content[:2] == b"\xff\xd8" and second.headers["cache-control"] == "no-store"
    assert client.get("/media/pending/missing").status_code == 404


def test_public_media_stays_available_while_publish_is_claimed(tmp_path, jpeg_bytes):
    import asyncio

    store = PendingPostStore(tmp_path)
    post = asyncio.run(store.create(1, 42, jpeg_bytes))
    app = FastAPI()
    app.include_router(create_media_router(store))
    client = TestClient(app)

    asyncio.run(store.claim(post.token, 42))
    response = client.get(f"/media/pending/{post.token}")

    assert response.status_code == 200
    assert response.content == jpeg_bytes

    asyncio.run(store.finish(post.token, True, {"post_id": "done"}))
    assert client.get(f"/media/pending/{post.token}").status_code == 404
