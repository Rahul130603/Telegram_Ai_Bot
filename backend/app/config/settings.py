from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Telegram AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"
    log_json: bool = False
    run_mode: Literal["polling", "webhook"] = "polling"
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_webhook_url: str = ""
    telegram_webhook_path: str = "/telegram/webhook"
    telegram_webhook_secret: SecretStr = SecretStr("")
    telegram_allowed_user_ids: str = ""
    telegram_parse_mode: Literal["none", "html", "markdown", "markdownv2"] = "none"
    telegram_max_message_length: int = Field(4000, ge=1, le=4096)

    ai_provider: Literal["deepseek", "openai", "openrouter", "groq", "together", "ollama", "gemini", "none"] = "deepseek"
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    ai_base_url: str = ""
    ai_temperature: float = Field(0.7, ge=0, le=2)
    ai_max_tokens: int = Field(1200, gt=0)
    ai_timeout_seconds: float = Field(60, gt=0)
    ai_max_retries: int = Field(2, ge=0, le=10)

    image_provider: Literal["pollinations", "openai", "gemini", "cloudflare", "stability", "none"] = "pollinations"
    image_api_key: SecretStr = SecretStr("")
    image_model: str = ""
    image_base_url: str = ""
    image_size: str = "1024x1024"
    image_timeout_seconds: float = Field(120, gt=0)
    image_max_retries: int = Field(2, ge=0, le=10)
    cloudflare_api_token: SecretStr = SecretStr("")
    cloudflare_account_id: str = ""

    agent_memory_turns: int = Field(8, ge=1, le=50)
    agent_memory_ttl_seconds: int = Field(3600, gt=0)
    rate_limit_messages: int = Field(20, gt=0)
    rate_limit_window_seconds: int = Field(60, gt=0)
    max_input_chars: int = Field(4000, ge=1, le=20000)
    startup_strict: bool = False
    http_max_retries: int = Field(2, ge=0, le=10)
    http_timeout_seconds: float = Field(30, gt=0)

    image_overlay_enabled: bool = True
    image_overlay_position: Literal["auto", "top", "center", "bottom"] = "auto"
    image_overlay_max_lines: int = Field(4, ge=1, le=10)
    image_overlay_font_path: str = ""

    social_enabled: bool = True
    pending_post_ttl_seconds: int = Field(1800, gt=0)
    social_max_pending_per_chat: int = Field(5, ge=1, le=50)
    social_pending_dir: str = ""
    social_public_base_url: str = ""
    meta_graph_version: str = "v21.0"
    instagram_login_flow: Literal["instagram", "facebook"] = "facebook"
    instagram_access_token: SecretStr = SecretStr("")
    instagram_business_account_id: str = ""
    facebook_access_token: SecretStr = SecretStr("")
    facebook_page_id: str = ""
    linkedin_access_token: SecretStr = SecretStr("")
    linkedin_author_urn: str = ""
    x_api_key: SecretStr = SecretStr("")
    x_api_secret: SecretStr = SecretStr("")
    x_access_token: SecretStr = SecretStr("")
    x_access_secret: SecretStr = SecretStr("")
    oauth_state_ttl_seconds: int = Field(600, gt=0)
    facebook_app_id: str = ""
    facebook_app_secret: SecretStr = SecretStr("")
    linkedin_client_id: str = ""
    linkedin_client_secret: SecretStr = SecretStr("")
    x_client_id: str = ""
    x_client_secret: SecretStr = SecretStr("")
    social_db_path: str = ""
    social_token_key: SecretStr = SecretStr("")

    @field_validator("image_size")
    @classmethod
    def valid_size(cls, value: str) -> str:
        try:
            width, height = (int(part) for part in value.lower().split("x", 1))
        except (TypeError, ValueError) as exc:
            raise ValueError("IMAGE_SIZE must be WIDTHxHEIGHT") from exc
        if not (64 <= width <= 4096 and 64 <= height <= 4096):
            raise ValueError("image dimensions must be between 64 and 4096")
        return f"{width}x{height}"

    @field_validator("telegram_webhook_path")
    @classmethod
    def path_starts_slash(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("webhook path must start with /")
        return value

    @model_validator(mode="after")
    def strict_requirements(self) -> Settings:
        if self.startup_strict and not self.telegram_bot_token.get_secret_value():
            raise ValueError("TELEGRAM_BOT_TOKEN is required in strict mode")
        return self

    @property
    def allowed_user_ids(self) -> set[int]:
        return {int(v.strip()) for v in self.telegram_allowed_user_ids.split(",") if v.strip()}

    @property
    def pending_dir(self) -> Path:
        return Path(self.social_pending_dir) if self.social_pending_dir else BASE_DIR / "tmp" / "pending"

    @property
    def db_path(self) -> Path:
        return Path(self.social_db_path) if self.social_db_path else BASE_DIR / "data" / "social.db"

    def safe_summary(self) -> dict[str, object]:
        return {
            "app_name": self.app_name,
            "environment": self.environment,
            "run_mode": self.run_mode,
            "ai_provider": self.ai_provider,
            "ai_configured": bool(self.ai_api_key.get_secret_value()) or self.ai_provider == "ollama",
            "image_provider": self.image_provider,
            "social_enabled": self.social_enabled,
            "public_base_configured": bool(self.social_public_base_url),
            "telegram_configured": bool(self.telegram_bot_token.get_secret_value()),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()

