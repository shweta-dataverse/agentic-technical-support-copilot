# central application configuration
# all runtime config is read from environment variables (12-factor style),
# with a local .env file supported for development.

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # service
    # ------------------------------------------------------------------
    app_name: str = "agentic-technical-support-copilot"
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"

    # simple shared-secret API key auth for the HTTP surface.
    # override in every real deployment.
    api_key: str = "dev-key-change-me"

    # ------------------------------------------------------------------
    # llm provider selection
    #   azure         -> Azure OpenAI Service    (GDPR/EU data residency)
    #   azure_foundry -> Azure AI Foundry models (Grok/Mistral/etc., serverless)
    #   anthropic     -> Claude API              (config-switchable)
    #   ollama        -> local models            (free/offline fallback)
    # ------------------------------------------------------------------
    llm_provider: Literal["azure", "azure_foundry", "anthropic", "ollama"] = "azure"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.2

    # Azure OpenAI Service — one resource, one endpoint/key; deployments are
    # names routed via the request path, not separate credentials.
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment: str = "gpt-5-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Azure AI Foundry (Models-as-a-Service, e.g. Grok, Mistral, Llama)
    azure_foundry_endpoint: str = ""
    azure_foundry_api_key: str = ""
    # deployment/model name; leave blank if the endpoint serves a single model
    azure_foundry_model: str = "grok-4-20-reasoning"

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # Ollama
    ollama_model: str = "llama3.1"
    ollama_host: str = "http://localhost:11434"

    # ------------------------------------------------------------------
    # embeddings — text-embedding-3-small on the Azure OpenAI resource
    # ------------------------------------------------------------------
    embedding_dim: int = 1536
    embedding_batch_size: int = 64

    # ------------------------------------------------------------------
    # ingestion — chunking and quality gates
    # ------------------------------------------------------------------
    chunk_size: int = 1000
    chunk_overlap: int = 150
    chunk_min_chars: int = 40
    ingest_max_reject_rate: float = 0.20

    # ------------------------------------------------------------------
    # Azure AI Search — hybrid retrieval indexes
    # ------------------------------------------------------------------
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""  # admin key; managed identity replaces this in cloud
    search_index_manuals: str = "manuals"
    search_index_tickets: str = "tickets"
    retrieval_k_manuals: int = 8
    retrieval_k_tickets: int = 5

    # ------------------------------------------------------------------
    # database (pgvector-enabled postgres)
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+psycopg://copilot:copilot@localhost:5432/jira_copilot",
        description="SQLAlchemy URL for the pgvector-enabled Postgres instance.",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — read once per process."""
    return Settings()
