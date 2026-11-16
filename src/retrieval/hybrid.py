import json
from pathlib import Path

from bm25 import BM25Index, load_chunks
from dense import DenseIndex



def rrf(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None):
    """Reciprocal Rank Fusion. weights = one weight per ranking (default: all 1.0)."""
    weights = weights or [1.0] * len(rankings)
    scores: dict[str, float] = {}
    for ranking, w in zip(rankings, weights):
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + w / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridIndex:
    def __init__(self, chunks: list[dict], pool: int = 30):
        self.by_id = {c["chunk_id"]: c for c in chunks}
        self.bm25 = BM25Index(chunks)
        self.dense = DenseIndex(chunks)
        self.pool = pool          # how many results to take from each retriever

    def search(self, query: str, k: int = 5) -> list[dict]:
        bm25_ids = [r["chunk_id"] for r in self.bm25.search(query, self.pool)]
        dense_ids = [r["chunk_id"] for r in self.dense.search(query, self.pool)]
        fused = rrf([bm25_ids, dense_ids])[:k]
        return [{**self.by_id[cid], "score": s} for cid, s in fused]


if __name__ == "__main__":
    index = HybridIndex(load_chunks())
    for q in [
        "What are Apple's supply chain risks?",
        "Tesla battery cell supply constraints",
        "NVIDIA export controls China",
    ]:
        print("\nQUERY:", q)
        for r in index.search(q, k=3):
            print(f"  {r['chunk_id']}  rrf={r['score']:.4f}")
            print("     ", r["text"][:150].replace("\n", " "))