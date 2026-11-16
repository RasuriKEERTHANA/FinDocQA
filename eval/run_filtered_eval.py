import json
import sys
from pathlib import Path

sys.path.insert(0, "src/retrieval")
from bm25 import BM25Index, load_chunks
from dense import DenseIndex
from hybrid import rrf
from filters import detect_tickers

K = 5
POOL = 100   # fetch more, then filter, so enough chunks survive


def filtered(results, query):
    tickers = detect_tickers(query)
    if not tickers:
        return results
    return [r for r in results if r["ticker"] in tickers]


def evaluate(name, search_fn, questions):
    hits, rr = 0, 0.0
    for q in questions:
        ids = [r["chunk_id"] for r in search_fn(q["question"])]
        relevant = set(q["relevant_chunks"])
        rank = next((i for i, cid in enumerate(ids, 1) if cid in relevant), None)
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
    by_id = {c["chunk_id"]: c for c in chunks}
    bm25, dense = BM25Index(chunks), DenseIndex(chunks)

    def bm25_f(q):
        return filtered(bm25.search(q, POOL), q)

    def dense_f(q):
        return filtered(dense.search(q, POOL), q)

    def hybrid_f(q):
        a = [r["chunk_id"] for r in bm25_f(q)[:30]]
        b = [r["chunk_id"] for r in dense_f(q)[:30]]
        return [by_id[cid] for cid, _ in rrf([a, b])]

    evaluate("BM25+F", bm25_f, questions)
    evaluate("Dense+F", dense_f, questions)
    evaluate("Hybrid+F", hybrid_f, questions)