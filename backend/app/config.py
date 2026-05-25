from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=["../.env", ".env"], extra="ignore")

    # Gemini
    gemini_api_key: str

    # Telegram
    telegram_bot_token: str
    telegram_webhook_url: str = ""

    # Tavily
    tavily_api_key: str

    # PostgreSQL
    database_url: str

    # Redis
    redis_url: str

    # App
    secret_key: str
    environment: str = "development"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
