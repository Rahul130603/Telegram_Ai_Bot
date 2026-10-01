from __future__ import annotations

import hashlib
import json
import logging
import re

SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(access_token|api_key|app_secret|password|code)=([^&\s]+)"),
    re.compile(r"(/media/pending/)[A-Za-z0-9_-]+"),
    re.compile(r"(?i)(/bot)\d{6,12}:[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?<!\w)\d{6,12}:[A-Za-z0-9_-]{20,}"),
]


def redact(value: object) -> str:
    text = str(value)
    text = SECRET_PATTERNS[0].sub(r"\1{secret}", text)
    text = SECRET_PATTERNS[1].sub(r"\1={secret}", text)
    text = SECRET_PATTERNS[2].sub(r"\1{token}", text)
    text = SECRET_PATTERNS[3].sub(r"\1{telegram-token}", text)
    return SECRET_PATTERNS[4].sub("{telegram-token}", text)


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "logger": record.name, "message": redact(record.getMessage())})


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler], force=True)
    for name in ("httpx", "httpcore", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.addFilter(RedactingFilter())
        logger.setLevel(logging.WARNING)

