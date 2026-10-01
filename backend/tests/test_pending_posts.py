import asyncio

import pytest

from app.social.pending import PendingPostStore
from app.utils.errors import SocialError


@pytest.mark.asyncio
async def test_owner_cancel_and_atomic_claim(tmp_path, png_bytes):
    store = PendingPostStore(tmp_path, 60, 2)
    post = await store.create(1, 10, png_bytes)
    results = await asyncio.gather(store.claim(post.token, 10), store.claim(post.token, 10), return_exceptions=True)
    assert sum(not isinstance(item, Exception) for item in results) == 1
    assert sum(isinstance(item, SocialError) for item in results) == 1

