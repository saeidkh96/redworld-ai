from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RedWorld AI"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    world_name: str = "Genesis"
    random_seed: int = 42

    model_config = SettingsConfigDict(
        env_prefix="REDWORLD_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
