from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://liaw:liaw_dev_pass@db:5432/liaw"

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 168  # 7 days

    # Meta / WhatsApp Cloud API
    META_PHONE_NUMBER_ID: str = ""
    META_ACCESS_TOKEN: str = ""
    META_VERIFY_TOKEN: str = ""
    META_APP_SECRET: str = ""

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
