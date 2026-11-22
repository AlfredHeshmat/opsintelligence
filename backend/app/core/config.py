from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpsIntelligence"
    database_url: SecretStr
    cors_origins: list[str] = ["http://localhost:5173"]
    ops_enable_local_signup: bool = False
    ops_allow_legacy_member_add: bool = False
    ops_public_demo_only: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
