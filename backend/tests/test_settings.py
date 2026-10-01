import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_safe_summary_contains_no_secrets():
    settings = Settings(_env_file=None, telegram_bot_token="secret", ai_api_key="key")
    text = str(settings.safe_summary())
    assert "secret" not in text and "key" not in text


def test_invalid_dimensions_and_defaults():
    assert Settings(_env_file=None).image_size == "1024x1024"
    with pytest.raises(ValidationError):
        Settings(_env_file=None, image_size="10x10")

