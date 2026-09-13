from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RedWorld AI"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    default_population: int = 1500
    world_seed: int = 20260912
    model_config = SettingsConfigDict(env_prefix="REDWORLD_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
