from pydantic_settings import BaseSettings

DEV_JWT_SECRET = "dev-only-secret-change-me-in-production-0123456789"


class Settings(BaseSettings):
    """App configuration. Values can be overridden via environment or .env."""

    # "development" allows insecure defaults; "production" refuses to start
    # without real secrets (see validate_for_production).
    environment: str = "development"

    database_url: str = "sqlite:///./collegecompass.db"
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Comma-separated origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Requests per window, per client IP, on sensitive endpoints.
    rate_limit_auth: int = 10        # login/register attempts
    rate_limit_ai: int = 20          # essay analyses + tutor messages
    rate_limit_window_seconds: int = 300

    # ---- AI provider ----
    # "auto" picks the best configured provider: anthropic -> openai_compat ->
    # ollama -> mock. Force one with LLM_PROVIDER=mock|anthropic|openai_compat|ollama.
    llm_provider: str = "auto"

    # Best quality, paid. https://console.anthropic.com
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"

    # Any OpenAI-compatible endpoint - Groq, Together, OpenRouter, DeepInfra.
    # Groq's free tier: base_url https://api.groq.com/openai/v1
    openai_compat_base_url: str = ""
    openai_compat_api_key: str = ""
    openai_compat_model: str = "llama-3.1-8b-instant"

    # Local Ollama - free, private, but only reachable from the machine it runs on.
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def cors_origin_list(s: "Settings | None" = None) -> list[str]:
    source = s or settings
    return [o.strip() for o in source.cors_origins.split(",") if o.strip()]


def validate_for_production(s: Settings | None = None) -> list[str]:
    """Return blocking misconfigurations for a public deployment.

    Called at startup when ENVIRONMENT=production; the app refuses to boot
    rather than silently serving students with forgeable auth tokens.
    """
    s = s or settings
    problems = []
    if s.jwt_secret == DEV_JWT_SECRET:
        problems.append(
            "JWT_SECRET is still the public dev default - anyone reading the source "
            'could forge a login for any student. Generate one with: python -c '
            "\"import secrets; print(secrets.token_urlsafe(48))\""
        )
    elif len(s.jwt_secret) < 32:
        problems.append("JWT_SECRET is too short - use at least 32 characters.")
    if s.database_url.startswith("sqlite"):
        problems.append(
            "DATABASE_URL is SQLite - most hosts have ephemeral disks, so every "
            "account and essay would be lost on redeploy. Use Postgres."
        )
    if any(o.startswith("http://localhost") for o in cors_origin_list(s)):
        problems.append("CORS_ORIGINS still contains localhost - set your real frontend origin.")
    return problems
