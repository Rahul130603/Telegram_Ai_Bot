from __future__ import annotations

import asyncio

from app.config.settings import get_settings
from app.social.instagram import InstagramProvider


async def main() -> int:
    settings = get_settings()
    provider = InstagramProvider(settings.instagram_access_token.get_secret_value(), settings.instagram_business_account_id, settings.instagram_login_flow, settings.meta_graph_version)
    print({"flow": settings.instagram_login_flow, "status": (await provider.get_status()).safe_message, "public_base_configured": bool(settings.social_public_base_url)})
    if provider.token and provider.account_id:
        status = await provider.authenticate()
        print({"authenticated": status.authenticated, "account_name": status.account_name})
    await provider.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

