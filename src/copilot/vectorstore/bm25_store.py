import json
from rank_bm25 import BM25Okapi
from pathlib import Path

class BM25Store:
    def __init__(self, texts, metadata):
        self.texts = texts
        self.metadata = metadata
        tokenized = [t.lower().split() for t in texts]
        self.bm25 = BM25Okapi(tokenized)

    @classmethod
    def load_from_metadata(cls, metadata_path: Path):
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        texts = [
            m.get("text", {}).get("text", "")
            for m in metadata
        ]
        return cls(texts, metadata)

    def search(self, query, k=5):
        scores = self.bm25.get_scores(query.lower().split())
        ranked_ids = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )
        return ranked_ids[:k]