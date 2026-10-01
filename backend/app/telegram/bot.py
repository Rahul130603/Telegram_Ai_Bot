from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application

from app.ai.agent import AIAgent
from app.config.settings import Settings
from app.image.base import ImageProvider
from app.social.connections import ConnectionStore
from app.social.oauth import OAuthManager
from app.social.pending import PendingPostStore
from app.social.service import SocialService
from app.utils.ratelimit import SlidingWindowRateLimiter

from .client import PTBTelegramClient
from .handlers import register_handlers

logger = logging.getLogger(__name__)


class BotRuntime:
    def __init__(self, settings: Settings, agent: AIAgent, image_provider: ImageProvider) -> None:
        self.settings, self.agent, self.image_provider = settings, agent, image_provider
        token = settings.telegram_bot_token.get_secret_value() or "123456789:TEST_TOKEN_FOR_DEGRADED_STARTUP"
        builder = Application.builder().token(token)
        if settings.run_mode == "webhook":
            builder = builder.updater(None)
        self.application = builder.build()
        self.client = PTBTelegramClient(self.application.bot, settings.telegram_max_message_length, settings.telegram_parse_mode)
        self.pending = PendingPostStore(settings.pending_dir, settings.pending_post_ttl_seconds, settings.social_max_pending_per_chat)
        self.connections = ConnectionStore(settings.db_path, settings.social_token_key.get_secret_value())
        self.social = SocialService(settings, self.pending, self.connections)
        self.oauth = OAuthManager(settings, self.connections)
        self.rate_limiter = SlidingWindowRateLimiter(settings.rate_limit_messages, settings.rate_limit_window_seconds)
        self.started = False
        register_handlers(self)

    async def start(self) -> None:
        if not self.settings.telegram_bot_token.get_secret_value():
            logger.warning("Telegram token missing; HTTP app starts in degraded mode")
            return
        await self.application.initialize()
        await self.application.start()
        if self.settings.run_mode == "polling":
            await self.application.bot.delete_webhook(drop_pending_updates=False)
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        self.started = True

    async def process_update(self, data: dict) -> None:
        if not self.started:
            raise RuntimeError("Telegram runtime is not ready")
        update = Update.de_json(data, self.application.bot)
        await self.application.process_update(update)

    async def stop(self) -> None:
        if self.started:
            if self.application.updater and self.application.updater.running:
                await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        await self.agent.llm.close()
        await self.image_provider.close()
        await self.oauth.close()
        self.started = False

