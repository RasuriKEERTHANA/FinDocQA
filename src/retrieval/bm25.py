import json
import re
from pathlib import Path
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    """Lowercase and split into word tokens (keeps numbers like 391,035)."""
    return re.findall(r"[a-z0-9][a-z0-9,\.]*[a-z0-9]|[a-z0-9]", text.lower())


class BM25Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])

    def search(self, query: str, k: int = 5) -> list[dict]:
        scores = self.bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in top]


def load_chunks(path: str = "data/processed/all_chunks.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    index = BM25Index(load_chunks())
    for q in [
        "What are Apple's supply chain risks?",
        "Tesla battery cell supply constraints",
        "NVIDIA export controls China",
    ]:
        print("\nQUERY:", q)
        for r in index.search(q, k=3):
            print(f"  {r['chunk_id']}  score={r['score']:.2f}")
            print("     ", r["text"][:150].replace("\n", " "))