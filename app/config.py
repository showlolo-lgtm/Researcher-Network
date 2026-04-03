from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./researcher_network.db"
    s2_api_key: str = ""
    refresh_cron: str = "0 0 * * 0"
    log_level: str = "INFO"
    relationship_tier_thresholds: list[int] = [5, 2, 1]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
