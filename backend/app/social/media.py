from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.utils.imaging import to_jpeg
from app.utils.logging import token_fingerprint

from .pending import PendingPostStore


def create_media_router(store: PendingPostStore) -> APIRouter:
    router = APIRouter()

    @router.get("/media/pending/{token}")
    async def pending_media(token: str) -> Response:
        # Confirming a post atomically moves it from pending to claimed before
        # the provider fetches the media. Keep the media available during that
        # publish window, but never expose terminal posts.
        post = store.get(token, include_terminal=True)
        if not post or post.status not in {"pending", "claimed"}:
            raise HTTPException(404, "media not found")
        data = to_jpeg(post.image_path.read_bytes())
        headers = {
            "Content-Length": str(len(data)),
            "Content-Disposition": f'inline; filename="image-{token_fingerprint(token)}.jpg"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        }
        return Response(data, media_type="image/jpeg", headers=headers)

    return router
