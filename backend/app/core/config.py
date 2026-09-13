from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "TintinHR"
    environment: str = "development"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    database_url: str = "postgresql+asyncpg://tintinhr:tintinhr@localhost:5432/tintinhr"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    llm_provider: str = "ollama"
    llm_model: str = "llama3.1:8b"
    llm_api_key: str = ""
    llm_base_url: str = "http://localhost:11434/v1"
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_reranker: bool = True
    vector_top_k: int = 20
    keyword_top_k: int = 20
    final_top_k: int = 6
    min_retrieval_score: float = 0.20
    max_upload_mb: int = 20

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        return [item.strip() for item in value.split(",")] if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

