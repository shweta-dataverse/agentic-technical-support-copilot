import numpy as np

class HybridRetriever:
    def __init__(self, faiss_store, bm25_store, embedder):
        self.faiss = faiss_store
        self.bm25 = bm25_store
        self.embedder = embedder

    def retrieve(self, query, k=5, alpha=0.5):
        # vector search
        q_emb = self.embedder.embed([query])[0]
        _, vec_ids = self.faiss.index.search(
            np.array([q_emb]), k
        )

        vector_ids = list(vec_ids[0])

        # keyword search
        bm25_ids = self.bm25.search(query, k)

        # merge + score
        score_map = {}

        for rank, idx in enumerate(vector_ids):
            score_map[idx] = score_map.get(idx, 0) + alpha * (k - rank)

        for rank, idx in enumerate(bm25_ids):
            score_map[idx] = score_map.get(idx, 0) + (1 - alpha) * (k - rank)

        # sort
        final_ids = sorted(
            score_map.keys(),
            key=lambda i: score_map[i],
            reverse=True
        )

        return [
            self.faiss.metadata[i]
            for i in final_ids[:k]
        ]