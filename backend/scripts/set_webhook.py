from __future__ import annotations

import asyncio

from telegram import Bot

from app.config.settings import get_settings


async def main() -> int:
    settings = get_settings()
    token = settings.telegram_bot_token.get_secret_value()
    if not token or not settings.telegram_webhook_url:
        print("TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL are required")
        return 1
    bot = Bot(token)
    await bot.set_webhook(settings.telegram_webhook_url.rstrip("/") + settings.telegram_webhook_path, secret_token=settings.telegram_webhook_secret.get_secret_value() or None)
    print("Webhook configured (URL/token intentionally hidden)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

