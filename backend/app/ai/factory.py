from __future__ import annotations

from app.config.settings import Settings
from app.utils.errors import ConfigurationError

from .base import LLMProvider
from .gemini import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider


class DisabledLLM(LLMProvider):
    @property
    def configured(self) -> bool:
        return False

    async def complete(self, messages, *, json_mode: bool = False) -> str:
        raise ConfigurationError("AI provider disabled")


def create_llm_provider(settings: Settings) -> LLMProvider:
    key = settings.ai_api_key.get_secret_value()
    if settings.ai_provider == "none":
        return DisabledLLM()
    if settings.ai_provider == "gemini":
        return GeminiProvider(key, settings.ai_model, settings.ai_base_url, settings.ai_timeout_seconds, settings.ai_max_retries)
    return OpenAICompatibleProvider(settings.ai_provider, key, settings.ai_model, settings.ai_base_url, settings.ai_temperature, settings.ai_max_tokens, settings.ai_timeout_seconds, settings.ai_max_retries)

