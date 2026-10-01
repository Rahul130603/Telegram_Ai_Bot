from __future__ import annotations

import argparse
import asyncio

from app.ai.factory import create_llm_provider
from app.config.settings import get_settings
from app.image.factory import create_image_provider


async def main() -> int:
    parser = argparse.ArgumentParser(description="Safe read-only setup check")
    parser.add_argument("--generate", action="store_true", help="Explicitly run one image generation (may incur provider cost)")
    args = parser.parse_args()
    settings = get_settings()
    llm, image = create_llm_provider(settings), create_image_provider(settings)
    print(settings.safe_summary())
    if args.generate:
        generated = await image.generate("simple blue circle on white background", settings.image_size)
        print({"generation_ok": True, "mime": generated.mime_type, "bytes": len(generated.data)})
    await llm.close()
    await image.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

