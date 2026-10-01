from __future__ import annotations

import asyncio

from telegram import Bot

from app.config.settings import get_settings


async def main() -> int:
    settings = get_settings()
    token = settings.telegram_bot_token.get_secret_value()
    if not token:
        print("TELEGRAM_BOT_TOKEN is required")
        return 1
    await Bot(token).delete_webhook(drop_pending_updates=False)
    print("Webhook deleted; pending updates retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

