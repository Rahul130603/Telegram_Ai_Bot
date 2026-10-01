from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError as exc:
        raise SystemExit("PORT must be an integer") from exc
    if not (1 <= port <= 65535):
        raise SystemExit("PORT must be between 1 and 65535")
    reload = os.getenv("RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run("app.main:app", host=host, port=port, reload=reload, access_log=False)


if __name__ == "__main__":
    main()

