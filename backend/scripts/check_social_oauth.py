from __future__ import annotations

from app.config.settings import get_settings
from app.social.connections import ConnectionStore
from app.social.oauth import OAuthManager


def main() -> int:
    settings = get_settings()
    manager = OAuthManager(settings, ConnectionStore(settings.db_path, settings.social_token_key.get_secret_value()))
    result = {"public_base_configured": bool(settings.social_public_base_url), "callbacks": {}}
    if settings.social_public_base_url:
        for platform in ("facebook", "linkedin", "x"):
            result["callbacks"][platform] = manager.redirect_uri(platform)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

