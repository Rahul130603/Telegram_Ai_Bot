from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import httpx

from .errors import ConfigurationError, NetworkError
from .imaging import validate_image
from .text import clean_wrapper


def _public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_unspecified)


def normalize_public_base_url(value: str) -> str:
    cleaned = unquote(clean_wrapper(value)).strip().rstrip("/")
    parsed = urlsplit(cleaned)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ConfigurationError("public base URL must be clean HTTPS without credentials")
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith(".local") or not _public_ip(host):
        raise ConfigurationError("public base URL host is not public")
    if "`" in cleaned or any(char in cleaned for char in '<>"'):
        raise ConfigurationError("public base URL contains formatting wrappers")
    return urlunsplit(("https", parsed.netloc, parsed.path.rstrip("/"), "", ""))


def build_media_url(base_url: str, token: str) -> str:
    if not token or "/" in token or token in {"{token}", "%7Btoken%7D"}:
        raise ValueError("invalid media token")
    return f"{normalize_public_base_url(base_url)}/media/pending/{token}"


async def resolve_public_addresses(host: str) -> list[str]:
    try:
        records = await __import__("asyncio").get_running_loop().run_in_executor(None, socket.getaddrinfo, host, 443)
    except OSError as exc:
        raise NetworkError("public media hostname DNS failed") from exc
    addresses = sorted({record[4][0] for record in records})
    if not addresses or any(not _public_ip(address) for address in addresses):
        raise ConfigurationError("public hostname resolves to non-public address")
    return addresses


@dataclass
class MediaProbe:
    status: int
    mime: str
    byte_length: int
    public_address_count: int


async def verify_public_media(url: str, client: httpx.AsyncClient | None = None) -> MediaProbe:
    normalized = normalize_public_base_url(url.rsplit("/media/pending/", 1)[0])
    host = urlsplit(normalized).hostname or ""
    addresses = await resolve_public_addresses(host)
    owned = client is None
    http = client or httpx.AsyncClient(timeout=20, follow_redirects=False)
    try:
        current = url
        for _ in range(4):
            response = await http.get(current)
            if response.is_redirect:
                target = urljoin(current, response.headers.get("location", ""))
                parsed = urlsplit(target)
                normalize_public_base_url(f"{parsed.scheme}://{parsed.netloc}")
                await resolve_public_addresses(parsed.hostname or "")
                current = target
                continue
            if response.status_code != 200:
                raise NetworkError(f"public media returned HTTP {response.status_code}")
            mime, _ = validate_image(response.content)
            if mime != response.headers.get("content-type", "").split(";", 1)[0]:
                raise NetworkError("public media MIME mismatch")
            return MediaProbe(response.status_code, mime, len(response.content), len(addresses))
        raise NetworkError("too many redirects")
    finally:
        if owned:
            await http.aclose()

