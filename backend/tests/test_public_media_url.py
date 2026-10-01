import pytest

from app.utils.errors import ConfigurationError
from app.utils.public_url import build_media_url, normalize_public_base_url


def test_real_token_interpolation_and_wrappers():
    assert build_media_url("`https://example.com/`", "abc") == "https://example.com/media/pending/abc"
    assert "{token}" not in build_media_url("https://example.com", "real")


@pytest.mark.parametrize("url", ["http://example.com", "https://localhost", "https://127.0.0.1", "https://user:pass@example.com"])
def test_rejects_non_public_base(url):
    with pytest.raises(ConfigurationError):
        normalize_public_base_url(url)

