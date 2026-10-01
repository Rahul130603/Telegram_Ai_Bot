from __future__ import annotations

from app.config.settings import Settings
from app.utils.errors import ConfigurationError

from .base import ImageProvider
from .cloudflare import CloudflareImageProvider
from .gemini_images import GeminiImageProvider
from .imagen import ImagenProvider
from .openai_images import OpenAIImageProvider
from .pollinations import PollinationsProvider
from .stability import StabilityImageProvider


class DisabledImageProvider(ImageProvider):
    @property
    def configured(self) -> bool:
        return False

    async def generate(self, prompt: str, size: str = "1024x1024"):
        raise ConfigurationError("image provider disabled")


def create_image_provider(settings: Settings) -> ImageProvider:
    provider = settings.image_provider
    key = settings.image_api_key.get_secret_value()
    args = (settings.image_model, settings.image_base_url, settings.image_timeout_seconds, settings.image_max_retries)
    if provider == "none":
        return DisabledImageProvider()
    if provider == "pollinations":
        return PollinationsProvider(key, *args)
    if provider == "openai":
        return OpenAIImageProvider(key, *args)
    if provider == "gemini":
        if settings.image_model.lower().startswith("imagen"):
            return ImagenProvider(key, settings.image_model, settings.image_base_url, settings.image_timeout_seconds, settings.image_max_retries)
        return GeminiImageProvider(key, *args)
    if provider == "cloudflare":
        return CloudflareImageProvider(settings.cloudflare_api_token.get_secret_value(), settings.cloudflare_account_id, settings.image_model, settings.image_timeout_seconds, settings.image_max_retries)
    return StabilityImageProvider(key, *args)

