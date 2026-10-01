from __future__ import annotations

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import ChatMessage, LLMProvider

DEFAULTS = {
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "openrouter": ("https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "together": ("https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    "ollama": ("http://127.0.0.1:11434/v1", "llama3.2"),
}


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, provider: str, api_key: str, model: str = "", base_url: str = "", temperature: float = 0.7, max_tokens: int = 1200, timeout: float = 60, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        default_url, default_model = DEFAULTS[provider]
        self.provider = provider
        self.api_key = api_key
        self.model = model or default_model
        self.base_url = (base_url or default_url).rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key) or self.provider == "ollama"

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        if not self.configured:
            raise ConfigurationError(f"{self.provider} API key missing")
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = await self.http.request("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload)
        if response.status_code >= 400:
            raise safe_status_error(response, "LLM completion")
        try:
            return str(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("malformed LLM response") from exc

    async def close(self) -> None:
        await self.http.close()

