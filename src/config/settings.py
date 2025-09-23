from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", yaml_file="config.yaml")
    ALLOWED_IDS: list[int] = [
        945651702,
        1287305857,  # me
    ]
    ADMIN_IDS: list[int] = [
        1287305857,  # me
    ]
    DEBUG: bool = False
    BOT_TOKEN: str = ""
    DB_URL: str = "sqlite+aiosqlite:///db.db"


settings = Settings()
