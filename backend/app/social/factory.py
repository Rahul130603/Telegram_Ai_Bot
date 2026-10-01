from __future__ import annotations

from app.config.settings import Settings

from .base import SocialMediaProvider
from .credentials import SocialCredentials
from .facebook import FacebookProvider
from .instagram import InstagramProvider
from .linkedin import LinkedInProvider
from .x import XProvider


def create_social_provider(platform: str, settings: Settings, credentials: SocialCredentials | None = None) -> SocialMediaProvider | None:
    token = credentials.access_token if credentials else ""
    account_id = credentials.account_id if credentials else ""
    if platform == "instagram":
        return InstagramProvider(token or settings.instagram_access_token.get_secret_value(), account_id or settings.instagram_business_account_id, settings.instagram_login_flow, settings.meta_graph_version)
    if platform == "facebook":
        return FacebookProvider(token or settings.facebook_access_token.get_secret_value(), account_id or settings.facebook_page_id, settings.meta_graph_version)
    if platform == "linkedin":
        return LinkedInProvider(token or settings.linkedin_access_token.get_secret_value(), account_id or settings.linkedin_author_urn)
    if platform == "x":
        return XProvider(settings.x_api_key.get_secret_value(), settings.x_api_secret.get_secret_value(), settings.x_access_token.get_secret_value(), settings.x_access_secret.get_secret_value(), token)
    return None

