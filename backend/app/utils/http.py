from __future__ import annotations

import asyncio
import logging

import httpx

from .errors import NetworkError, ProviderError, ProviderTimeout
from .logging import redact

logger = logging.getLogger(__name__)


class SafeHTTPClient:
    def __init__(self, timeout: float = 30, retries: int = 2, client: httpx.AsyncClient | None = None) -> None:
        self.retries = retries
        self._owned = client is None
        self.client = client or httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    async def request(self, method: str, url: str, *, side_effect: bool = False, **kwargs: object) -> httpx.Response:
        attempts = 1 if side_effect else self.retries + 1
        for attempt in range(attempts):
            try:
                response = await self.client.request(method, url, **kwargs)
            except httpx.TimeoutException as exc:
                if attempt + 1 == attempts:
                    raise ProviderTimeout("request timed out") from exc
            except httpx.HTTPError as exc:
                if attempt + 1 == attempts:
                    raise NetworkError("provider network error") from exc
            else:
                if response.status_code not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
                    return response
                retry_after = response.headers.get("retry-after", "")
                delay = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else 0.25 * (2**attempt)
                await asyncio.sleep(min(delay, 5))
                continue
            await asyncio.sleep(min(0.25 * (2**attempt), 5))
        raise ProviderError("request attempts exhausted")

    async def close(self) -> None:
        if self._owned:
            await self.client.aclose()


def safe_status_error(response: httpx.Response, operation: str) -> ProviderError:
    logger.warning("%s failed status=%s url=%s", operation, response.status_code, redact(str(response.request.url)))
    return ProviderError(f"{operation} failed with HTTP {response.status_code}")

