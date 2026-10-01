from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, urlsplit


def _escape(value: object) -> str:
    return quote(str(value), safe="~-._")


def oauth1_authorization(method: str, url: str, params: dict[str, object], consumer_key: str, consumer_secret: str, access_token: str, access_secret: str, *, nonce: str | None = None, timestamp: int | None = None) -> str:
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(timestamp or int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    combined = {**params, **oauth}
    parameter_string = "&".join(f"{_escape(k)}={_escape(v)}" for k, v in sorted(combined.items()))
    parsed = urlsplit(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    base = "&".join((_escape(method.upper()), _escape(base_url), _escape(parameter_string)))
    key = f"{_escape(consumer_secret)}&{_escape(access_secret)}"
    oauth["oauth_signature"] = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_escape(k)}="{_escape(v)}"' for k, v in sorted(oauth.items()))

