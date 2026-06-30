from pydantic_settings import BaseSettings
from functools import lru_cache

_INSECURE_DEFAULT = "change-me-in-production-use-a-long-random-string"


class Settings(BaseSettings):
    app_name: str = "Prism API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Security — must be set to a strong random value in production
    secret_key: str = _INSECURE_DEFAULT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./prism.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **values):
        super().__init__(**values)
        if not self.debug and self.secret_key == _INSECURE_DEFAULT:
            raise RuntimeError(
                "SECRET_KEY is not set. "
                "Generate one with: openssl rand -hex 32"
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
