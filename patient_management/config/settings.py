
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    secret_key: str

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 30

    internal_service_token: str
    reminder_hours_before: int = 24

    # OpenAI configuration is optional at application startup so the clinical
    # CRUD API continues to work when the RAG feature has not been configured.
    # The RAG service validates the key immediately before making an API call.
    openai_api_key: str | None = None
    openai_rag_model: str = "gpt-4o-mini"
    openai_agent_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
