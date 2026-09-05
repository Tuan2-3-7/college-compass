from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration. Values can be overridden via environment or .env."""

    database_url: str = "sqlite:///./collegecompass.db"
    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

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
