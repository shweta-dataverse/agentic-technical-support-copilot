"""Batched embeddings via the Azure OpenAI text-embedding-3-small deployment."""

from __future__ import annotations

from openai import AzureOpenAI

from copilot.config import get_settings
from copilot.exceptions import DownstreamUnavailableError


class AzureEmbedder:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise DownstreamUnavailableError("azure openai credentials not configured")
        self._deployment = settings.azure_openai_embedding_deployment
        self._batch_size = settings.embedding_batch_size
        self._client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            timeout=60.0,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in order, batching requests to respect payload limits."""
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            response = self._client.embeddings.create(
                model=self._deployment, input=batch
            )
            # API may return out of order; index field restores it
            ordered = sorted(response.data, key=lambda d: d.index)
            vectors.extend(d.embedding for d in ordered)
        return vectors
