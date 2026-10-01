from __future__ import annotations

import httpx

from app.utils.errors import ConfigurationError, ProviderError
from app.utils.http import SafeHTTPClient, safe_status_error

from .base import ChatMessage, LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", base_url: str = "https://generativelanguage.googleapis.com/v1beta", timeout: float = 60, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.http = SafeHTTPClient(timeout, retries, client)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        if not self.configured:
            raise ConfigurationError("Gemini API key missing")
        system = "\n".join(message.content for message in messages if message.role == "system")
        contents = [{"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]} for m in messages if m.role != "system"]
        payload: dict[str, object] = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
        url = f"{self.base_url}/models/{self.model}:generateContent"
        response = await self.http.request("POST", url, headers={"x-goog-api-key": self.api_key}, json=payload)
        if response.status_code >= 400:
            raise safe_status_error(response, "Gemini completion")
        try:
            return "".join(part.get("text", "") for part in response.json()["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("Gemini returned no text") from exc

    async def close(self) -> None:
        await self.http.close()

