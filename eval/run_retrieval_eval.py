import json
import sys
from pathlib import Path

sys.path.insert(0, "src/retrieval")
from bm25 import BM25Index, load_chunks
from dense import DenseIndex
from hybrid import rrf

K = 5

def evaluate(name, search_fn, questions):
    hits, rr = 0, 0.0
    for q in questions:
        results = [r["chunk_id"] for r in search_fn(q["question"])]
        relevant = set(q["relevant_chunks"])
        rank = next((i for i, cid in enumerate(results, 1) if cid in relevant), None)
        if rank and rank <= K:
            hits += 1
        if rank:
            rr += 1.0 / rank
    n = len(questions)
    print(f"{name:8s} hit-rate@{K} = {hits/n:.0%}   MRR = {rr/n:.3f}   (n={n})")

if __name__ == "__main__":
    questions = [q for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
                 if q["type"] == "text" and q["relevant_chunks"]]
    chunks = load_chunks()
    bm25, dense = BM25Index(chunks), DenseIndex(chunks)

    def hybrid(query):
        a = [r["chunk_id"] for r in bm25.search(query, 30)]
        b = [r["chunk_id"] for r in dense.search(query, 30)]
        by_id = {c["chunk_id"]: c for c in chunks}
        return [by_id[cid] for cid, _ in rrf([a, b])]

    evaluate("BM25", lambda q: bm25.search(q, 30), questions)
    evaluate("Dense", lambda q: dense.search(q, 30), questions)
    evaluate("Hybrid", hybrid, questions)