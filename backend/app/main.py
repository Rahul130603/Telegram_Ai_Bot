from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.ai.agent import AIAgent
from app.ai.factory import create_llm_provider
from app.ai.memory import ConversationMemory
from app.config.settings import Settings, get_settings
from app.image.factory import create_image_provider
from app.social.media import create_media_router
from app.social.oauth_routes import create_oauth_router
from app.telegram.bot import BotRuntime
from app.telegram.webhook import create_webhook_router
from app.utils.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()
    configure_logging(configured.log_level, configured.log_json)
    llm = create_llm_provider(configured)
    image = create_image_provider(configured)
    memory = ConversationMemory(configured.agent_memory_turns, configured.agent_memory_ttl_seconds)
    agent = AIAgent(llm, memory, configured.max_input_chars)
    runtime = BotRuntime(configured, agent, image)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.runtime = runtime
        application.state.background_updates = set()
        await runtime.start()
        try:
            yield
        finally:
            tasks = list(application.state.background_updates)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            await runtime.stop()

    application = FastAPI(title=configured.app_name, version="1.0.0", lifespan=lifespan)
    application.state.runtime = runtime
    application.state.background_updates = set()
    application.include_router(create_media_router(runtime.pending))
    application.include_router(create_oauth_router(runtime.oauth))
    application.include_router(create_webhook_router(runtime))

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"name": configured.app_name, "status": "running"}

    @application.get("/health")
    async def health() -> dict[str, object]:
        return {"live": True, "ready": bool(runtime.started), "configuration": configured.safe_summary()}

    @application.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"live": True}

    @application.get("/readyz")
    async def readyz():
        reasons = []
        if not configured.telegram_bot_token.get_secret_value():
            reasons.append("telegram token missing")
        if not llm.configured:
            reasons.append("AI provider not configured")
        if not image.configured:
            reasons.append("image provider not configured")
        ready = runtime.started and not reasons
        payload = {"ready": ready, "degraded_reasons": reasons}
        return payload if ready else JSONResponse(payload, status_code=503)

    return application


app = create_app()

