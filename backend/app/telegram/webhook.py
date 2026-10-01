from __future__ import annotations

import asyncio
import hmac

from fastapi import APIRouter, Header, HTTPException, Request, Response


def create_webhook_router(runtime) -> APIRouter:
    router = APIRouter()
    path = runtime.settings.telegram_webhook_path

    @router.post(path)
    async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header("")) -> Response:
        expected = runtime.settings.telegram_webhook_secret.get_secret_value()
        if expected and not hmac.compare_digest(expected, x_telegram_bot_api_secret_token):
            raise HTTPException(403, "invalid webhook secret")
        try:
            data = await request.json()
        except ValueError as exc:
            raise HTTPException(400, "invalid JSON") from exc
        if not isinstance(data, dict) or "update_id" not in data:
            raise HTTPException(400, "invalid Telegram update")
        task = asyncio.create_task(runtime.process_update(data))
        request.app.state.background_updates.add(task)
        task.add_done_callback(request.app.state.background_updates.discard)
        return Response(status_code=204)

    return router

