import json
import sys
from pathlib import Path

sys.path.insert(0, "src/retrieval")
from bm25 import BM25Index, load_chunks
from dense import DenseIndex
from hybrid import rrf
from filters import detect_tickers

K, POOL = 5, 100


def filtered(results, query):
    tickers = detect_tickers(query)
    return [r for r in results if r["ticker"] in tickers] if tickers else results


def report(name, results, q):
    ids = [r["chunk_id"] for r in results]
    relevant = set(q["relevant_chunks"])
    rank = next((i for i, cid in enumerate(ids, 1) if cid in relevant), None)
    if rank and rank <= K:
        return
    print("=" * 80)
    print(f"[{name}] {q['id']}: {q['question']}")
    print("  labeled:", sorted(relevant))
    print("  first correct rank:", rank if rank else f"not in top {len(ids)}")
    print("  returned top 5:")
    for r in results[:K]:
        print("   ", r["chunk_id"], "|", r["text"][:100].replace("\n", " "))


if __name__ == "__main__":
    questions = [q for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
                 if q["type"] == "text" and q["relevant_chunks"]]
    chunks = load_chunks()
    by_id = {c["chunk_id"]: c for c in chunks}
    bm25, dense = BM25Index(chunks), DenseIndex(chunks)

    for q in questions:
        text = q["question"]
        b = filtered(bm25.search(text, POOL), text)
        d = filtered(dense.search(text, POOL), text)
        h = [by_id[cid] for cid, _ in rrf([[r["chunk_id"] for r in b[:30]],
                                           [r["chunk_id"] for r in d[:30]]])]
        report("BM25+F", b, q)
        report("Dense+F", d, q)
        report("Hybrid+F", h, q)