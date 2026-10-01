from urllib.parse import parse_qs, urlsplit

import pytest

from app.config.settings import Settings
from app.social.connections import ConnectionStore
from app.social.oauth import OAuthManager, OAuthStateStore
from app.utils.errors import AuthenticationError


def test_state_is_owner_bound_expiring_and_single_use():
    states = OAuthStateStore(60)
    created = states.create("facebook", 42, "https://example.com/auth/facebook/callback")
    assert states.consume(created.value, "facebook").user_id == 42
    with pytest.raises(AuthenticationError):
        states.consume(created.value, "facebook")


@pytest.mark.parametrize("platform", ["facebook", "linkedin", "x"])
def test_consent_redirect_is_clean_and_exact(tmp_path, platform):
    settings = Settings(_env_file=None, social_public_base_url="https://bot.example.com", facebook_app_id="fb", linkedin_client_id="li", x_client_id="x")
    manager = OAuthManager(settings, ConnectionStore(tmp_path / "db"))
    url = manager.consent_url(platform, 1)
    redirect = parse_qs(urlsplit(url).query)["redirect_uri"][0]
    assert redirect == f"https://bot.example.com/auth/{platform}/callback"
    assert "`" not in redirect and "%60" not in url


