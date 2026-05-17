from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://liaw:liaw_dev_pass@db:5432/liaw"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _ensure_asyncpg_driver(cls, v: str) -> str:
        # Railway's Postgres plugin hands out postgresql:// — SQLAlchemy's async
        # engine needs the +asyncpg driver suffix. Normalise here so every
        # caller (engine, Alembic) can use settings.DATABASE_URL unchanged.
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 168  # 7 days

    # Odyssey Gateway — used for sending WhatsApp replies and validating inbound webhooks.
    ODYSSEY_URL: str = "http://host.docker.internal:3000"
    ODYSSEY_API_KEY: str = "your_super_secret_api_key_here"       # must match GATEWAY_API_KEY on the Odyssey side
    ODYSSEY_WEBHOOK_SECRET: str = "LIAW_WEBHOOK_SECRET" # must match webhook_secret in Odyssey config.json

    # Meta / WhatsApp Cloud API — commented out; replaced by Odyssey integration.
    # META_PHONE_NUMBER_ID: str = ""
    # META_ACCESS_TOKEN: str = ""
    # META_VERIFY_TOKEN: str = ""
    # META_APP_SECRET: str = ""

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
