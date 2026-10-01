from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.config.settings import get_settings
from app.social.pending import PendingPostStore
from app.utils.logging import token_fingerprint
from app.utils.public_url import build_media_url, verify_public_media


async def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in exact public media route probe; never publishes")
    parser.add_argument("image", type=Path)
    parser.add_argument("--telegram-user-id", type=int, default=0)
    args = parser.parse_args()
    settings = get_settings()
    store = PendingPostStore(settings.pending_dir, settings.pending_post_ttl_seconds, settings.social_max_pending_per_chat)
    post = await store.create(args.telegram_user_id, args.telegram_user_id, args.image.read_bytes())
    url = build_media_url(settings.social_public_base_url, post.token)
    print({"token_fingerprint": token_fingerprint(post.token), "file_exists": post.image_path.exists(), "ttl_seconds": settings.pending_post_ttl_seconds, "public_host": url.split("/")[2]})
    probe = await verify_public_media(url)
    print({"reachable": True, "status": probe.status, "mime": probe.mime, "bytes": probe.byte_length, "public_addresses": probe.public_address_count})
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

