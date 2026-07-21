"""Create/update the AI Search indexes defined in copilot.retrieval.indexes.

Run after the search service exists: python scripts/create_search_indexes.py
"""

from __future__ import annotations

import sys

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient

from copilot.config import get_settings
from copilot.retrieval.indexes import ensure_indexes


def main() -> int:
    s = get_settings()
    if not s.azure_search_endpoint or not s.azure_search_api_key:
        print("FAIL: AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_API_KEY not set in .env")
        return 1

    client = SearchIndexClient(
        endpoint=s.azure_search_endpoint,
        credential=AzureKeyCredential(s.azure_search_api_key),
    )
    for name in ensure_indexes(client):
        stats = client.get_index_statistics(name)
        print(f"index OK: {name} (documents={stats['documentCount']})")
    print("all indexes ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
