from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    app_name: str = "Secure AI Insights Assistant"

    jwt_secret: str
    jwt_alg: str = "HS256"
    jwt_audience: str = "secure-ai-insights"
    jwt_issuer: str = "secure-ai-insights-api"
    jwt_nbf_skew_seconds: int = 0
    jwt_ttl_seconds: int = 300

    demo_data_dir: str = "demo_data"

    log_level: str = "INFO"

    # sentence_transformers | openai | local_hash — default avoids Groq (no embeddings API).
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    llm_provider: str = "groq"

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-70b-versatile"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    frontend_origin: str = "http://localhost:3000"

    # SQLite auth (relative paths are resolved from the backend working directory).
    auth_db_path: str = "data/auth.db"
    admin_email: str = "adminlocalhost@gmail.com"
    admin_password: str = "admin"


settings = Settings()  # type: ignore[call-arg]
