import json
import sys
from pathlib import Path

sys.path.insert(0, "src/retrieval")
from bm25 import BM25Index, load_chunks
from dense import DenseIndex
from hybrid import rrf
from filters import detect_tickers

K, POOL = 5, 100
WEIGHTS = [(1, 1), (1, 2), (1, 3), (2, 1)]   # (bm25, dense)


def filtered(results, query):
    tickers = detect_tickers(query)
    return [r for r in results if r["ticker"] in tickers] if tickers else results


if __name__ == "__main__":
    questions = [q for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
                 if q["type"] == "text" and q["relevant_chunks"]]
    chunks = load_chunks()
    bm25, dense = BM25Index(chunks), DenseIndex(chunks)

    # search once per question, reuse for every weight setting
    cache = {}
    for q in questions:
        t = q["question"]
        cache[q["id"]] = (
            [r["chunk_id"] for r in filtered(bm25.search(t, POOL), t)[:30]],
            [r["chunk_id"] for r in filtered(dense.search(t, POOL), t)[:30]],
        )

    for wb, wd in WEIGHTS:
        hits, rr = 0, 0.0
        for q in questions:
            a, b = cache[q["id"]]
            ids = [cid for cid, _ in rrf([a, b], weights=[wb, wd])]
            relevant = set(q["relevant_chunks"])
            rank = next((i for i, c in enumerate(ids, 1) if c in relevant), None)
            if rank and rank <= K:
                hits += 1
            if rank:
                rr += 1.0 / rank
        n = len(questions)
        print(f"bm25={wb} dense={wd}   hit@{K} = {hits/n:.0%}   MRR = {rr/n:.3f}   (n={n})")