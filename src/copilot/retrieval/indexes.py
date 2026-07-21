"""
Defines and creates the two AI Search indexes, manuals and tickets. Both are hybrid keyword
plus vector.
"""

from __future__ import annotations

from azure.core.exceptions import HttpResponseError
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from copilot.config import get_settings
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

VECTOR_PROFILE = "hnsw-default"


def _vector_search() -> VectorSearch:
    return VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE, algorithm_configuration_name="hnsw-config"
            )
        ],
    )


def _content_vector(dimensions: int) -> SearchField:
    return SearchField(
        name="content_vector",
        type="Collection(Edm.Single)",
        searchable=True,
        vector_search_dimensions=dimensions,
        vector_search_profile_name=VECTOR_PROFILE,
    )


def manuals_index(name: str, dimensions: int) -> SearchIndex:
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(name="chunk_id", type="Edm.String", key=True),
            SearchableField(name="content", type="Edm.String"),
            _content_vector(dimensions),
            SimpleField(
                name="doc_id", type="Edm.String", filterable=True
            ),
            SearchableField(name="doc_title", type="Edm.String"),
            SimpleField(
                name="page", type="Edm.Int32", filterable=True
            ),
            SearchableField(name="section_title", type="Edm.String"),
            SimpleField(
                name="ingested_at",
                type="Edm.DateTimeOffset",
                filterable=True,
            ),
        ],
        vector_search=_vector_search(),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="manuals-semantic",
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="section_title"),
                        content_fields=[SemanticField(field_name="content")],
                    ),
                )
            ]
        ),
    )


def tickets_index(name: str, dimensions: int) -> SearchIndex:
    return SearchIndex(
        name=name,
        fields=[
            SimpleField(name="ticket_id", type="Edm.String", key=True),
            SearchableField(name="summary", type="Edm.String"),
            SearchableField(name="description", type="Edm.String"),
            SearchableField(name="resolution_text", type="Edm.String"),
            _content_vector(dimensions),
            SimpleField(
                name="category", type="Edm.String", filterable=True
            ),
            SimpleField(
                name="severity", type="Edm.String", filterable=True
            ),
            SimpleField(
                name="status", type="Edm.String", filterable=True
            ),
            SimpleField(
                name="created_at",
                type="Edm.DateTimeOffset",
                filterable=True,
                sortable=True,
            ),
        ],
        vector_search=_vector_search(),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="tickets-semantic",
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="summary"),
                        content_fields=[
                            SemanticField(field_name="description"),
                            SemanticField(field_name="resolution_text"),
                        ],
                    ),
                )
            ]
        ),
    )


def ensure_indexes(client: SearchIndexClient) -> list[str]:
    """Create or update both indexes. Idempotent, safe to run repeatedly.

    Falls back to creating without the semantic configuration on SKUs that
    reject it (Free tier), logging the degradation instead of failing.
    """
    settings = get_settings()
    created: list[str] = []
    for index in (
        manuals_index(settings.search_index_manuals, settings.embedding_dim),
        tickets_index(settings.search_index_tickets, settings.embedding_dim),
    ):
        try:
            client.create_or_update_index(index)
        except HttpResponseError as exc:
            if "semantic" not in str(exc).lower():
                raise
            logger.warning(
                "semantic ranker not supported on this sku; creating %s without it",
                index.name,
            )
            index.semantic_search = None
            client.create_or_update_index(index)
        created.append(index.name)
    return created
