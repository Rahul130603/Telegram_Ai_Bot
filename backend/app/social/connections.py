from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .credentials import SocialCredentials

logger = logging.getLogger(__name__)


class ConnectionStore:
    def __init__(self, db_path: Path, token_key: str = "") -> None:
        self.db_path = db_path
        self._memory: dict[tuple[int, str], SocialCredentials] = {}
        self._fernet: Fernet | None = None
        if token_key:
            self._fernet = Fernet(token_key.encode())
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(db_path) as connection:
                connection.execute("CREATE TABLE IF NOT EXISTS connections (user_id INTEGER, platform TEXT, payload BLOB NOT NULL, PRIMARY KEY(user_id, platform))")
        else:
            logger.warning("SOCIAL_TOKEN_KEY missing; connections are memory-only and disappear on restart")

    @property
    def persistent(self) -> bool:
        return self._fernet is not None

    def set(self, user_id: int, credentials: SocialCredentials) -> None:
        key = (user_id, credentials.platform)
        self._memory[key] = credentials
        if self._fernet:
            encrypted = self._fernet.encrypt(json.dumps(credentials.payload()).encode())
            with sqlite3.connect(self.db_path) as connection:
                connection.execute("INSERT OR REPLACE INTO connections(user_id, platform, payload) VALUES (?, ?, ?)", (user_id, credentials.platform, encrypted))

    def get(self, user_id: int, platform: str) -> SocialCredentials | None:
        key = (user_id, platform)
        if key in self._memory:
            value = self._memory[key]
            return None if value.expired else value
        if not self._fernet:
            return None
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute("SELECT payload FROM connections WHERE user_id=? AND platform=?", (user_id, platform)).fetchone()
        if not row:
            return None
        try:
            value = SocialCredentials(**json.loads(self._fernet.decrypt(row[0])))
        except (InvalidToken, ValueError, TypeError, json.JSONDecodeError):
            logger.error("Encrypted connection could not be read user=%s platform=%s", user_id, platform)
            return None
        if value.expired:
            return None
        self._memory[key] = value
        return value

    def delete(self, user_id: int, platform: str) -> None:
        self._memory.pop((user_id, platform), None)
        if self._fernet:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute("DELETE FROM connections WHERE user_id=? AND platform=?", (user_id, platform))

