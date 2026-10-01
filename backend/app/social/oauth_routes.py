from __future__ import annotations

import html
import logging

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.utils.errors import AppError

from .oauth import OAuthManager

logger = logging.getLogger(__name__)


def create_oauth_router(manager: OAuthManager) -> APIRouter:
    router = APIRouter()

    @router.get("/auth/{platform}/callback", response_class=HTMLResponse)
    async def callback(platform: str, code: str = Query(""), state: str = Query(""), error: str = Query("")) -> HTMLResponse:
        logger.info("OAuth callback path platform=%s query_names=%s code_present=%s state_present=%s", platform, sorted(name for name, value in {"code": code, "state": state, "error": error}.items() if value), bool(code), bool(state))
        if platform not in {"facebook", "linkedin", "x"}:
            return HTMLResponse("<h1>Unsupported platform</h1>", 404)
        if error or not code or not state:
            return HTMLResponse("<h1>Connection not completed</h1><p>Missing or denied authorization.</p>", 400)
        try:
            credentials = await manager.callback(platform, code, state)
        except AppError as exc:
            return HTMLResponse(f"<h1>Connection failed</h1><p>{html.escape(exc.safe_message)}</p>", 400)
        summary = credentials.safe_summary()
        name = html.escape(str(summary.get("account_name") or summary.get("account_id") or platform))
        return HTMLResponse(f"<h1>Connected</h1><p>{html.escape(platform.title())}: {name}. You can close this tab.</p>")

    return router

