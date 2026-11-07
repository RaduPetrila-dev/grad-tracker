from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """ App settings, read from environment variables or from the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://tracker@localhost:5432/tracker"
    reed_api_key: str = ""
    admin_api_key: str = ""


settings = Settings()

