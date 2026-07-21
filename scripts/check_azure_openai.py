"""Smoke-check the Azure OpenAI setup in .env.

Verifies both deployments on the resource with one minimal call each:
  1. chat deployment answers a trivial prompt
  2. embedding deployment returns a vector of the configured dimension

Run: python scripts/check_azure_openai.py
"""

from __future__ import annotations

import sys

from openai import AzureOpenAI

from copilot.config import get_settings


def main() -> int:
    s = get_settings()
    if not s.azure_openai_endpoint or not s.azure_openai_api_key:
        print("FAIL: AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY not set in .env")
        return 1

    client = AzureOpenAI(
        azure_endpoint=s.azure_openai_endpoint,
        api_key=s.azure_openai_api_key,
        api_version=s.azure_openai_api_version,
    )

    print(f"endpoint:   {s.azure_openai_endpoint}")
    print(f"api ver:    {s.azure_openai_api_version}")

    # 1) chat deployment
    try:
        chat = client.chat.completions.create(
            model=s.azure_openai_deployment,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            max_completion_tokens=500,
        )
        text = (chat.choices[0].message.content or "").strip()
        print(f"chat:       OK  deployment={s.azure_openai_deployment!r} reply={text!r}")
    except Exception as exc:  # noqa: BLE001 — diagnostic script, report and exit
        print(f"chat:       FAIL deployment={s.azure_openai_deployment!r}: {exc}")
        return 1

    # 2) embedding deployment
    try:
        emb = client.embeddings.create(
            model=s.azure_openai_embedding_deployment,
            input="SIMATIC S7-1500 diagnostics",
        )
        dim = len(emb.data[0].embedding)
        status = "OK " if dim == s.embedding_dim else "WARN dimension mismatch"
        print(
            f"embeddings: {status} deployment={s.azure_openai_embedding_deployment!r} "
            f"dim={dim} (expected {s.embedding_dim})"
        )
        if dim != s.embedding_dim:
            return 1
    except Exception as exc:  # noqa: BLE001 — diagnostic script, report and exit
        print(f"embeddings: FAIL deployment={s.azure_openai_embedding_deployment!r}: {exc}")
        return 1

    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
