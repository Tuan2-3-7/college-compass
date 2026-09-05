from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration. Values can be overridden via environment or .env."""

    database_url: str = "sqlite:///./collegecompass.db"
    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

    # When set (backend/.env), AI features use the real Claude API instead of
    # the deterministic mock provider.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
