import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class DenseIndex:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.model = SentenceTransformer(MODEL_NAME)
        emb = self.model.encode(
            [c["text"] for c in chunks],
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        self.index = faiss.IndexFlatIP(emb.shape[1])   # inner product = cosine (normalized)
        self.index.add(np.asarray(emb, dtype="float32"))

    def search(self, query: str, k: int = 5) -> list[dict]:
        q = self.model.encode([QUERY_PREFIX + query], normalize_embeddings=True)
        scores, ids = self.index.search(np.asarray(q, dtype="float32"), k)
        return [{**self.chunks[i], "score": float(s)} for s, i in zip(scores[0], ids[0])]


def load_chunks(path: str = "data/processed/all_chunks.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    index = DenseIndex(load_chunks())
    for q in [
        "What are Apple's supply chain risks?",
        "Tesla battery cell supply constraints",
        "NVIDIA export controls China",
    ]:
        print("\nQUERY:", q)
        for r in index.search(q, k=3):
            print(f"  {r['chunk_id']}  score={r['score']:.3f}")
            print("     ", r["text"][:150].replace("\n", " "))