from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class SocialCredentials:
    platform: str
    access_token: str
    account_id: str
    account_name: str = ""
    account_kind: str = ""
    parent_id: str = ""
    refresh_token: str = ""
    expires_at: float | None = None
    scope: str = ""

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(timezone.utc).timestamp()

    def safe_summary(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "account_kind": self.account_kind,
            "parent_id": self.parent_id,
            "expires_at": self.expires_at,
            "scope": self.scope,
            "expired": self.expired,
        }

    def payload(self) -> dict[str, object]:
        return asdict(self)

