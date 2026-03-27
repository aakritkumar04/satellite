from pydantic_settings import BaseSettings
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """
    Configuration settings for the application loaded from environment variables.
    """
    DB_URL: str
    LOG_DIR: str = "log"
    LOG_FILE: str = "logs.txt"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
