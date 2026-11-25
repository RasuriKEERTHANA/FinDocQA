import sys

sys.path.insert(0, "src/retrieval")
sys.path.insert(0, "src/agent")
sys.path.insert(0, "src")

from bm25 import BM25Index, load_chunks
from dense import DenseIndex
from hybrid import rrf
from filters import detect_tickers
from llm import generate

TOP_K = 5
POOL = 100

PROMPT = """You answer questions about SEC 10-K filings using ONLY the passages below.

Rules:
1. Use only information in the passages. Do not use outside knowledge.
2. After every claim, cite the passage ID in square brackets, like [AAPL_2026_1A_003].
3. If the passages do not contain the answer, reply exactly: I don't know based on the provided filings.
4. Keep the answer under 120 words.

PASSAGES:
{passages}

QUESTION: {question}

ANSWER:"""


class Retriever:
    def __init__(self):
        self.chunks = load_chunks()
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self.bm25 = BM25Index(self.chunks)
        self.dense = DenseIndex(self.chunks)

    def search(self, question: str, k: int = TOP_K) -> list[dict]:
        tickers = detect_tickers(question)

        def keep(rs):
            return [r for r in rs if r["ticker"] in tickers] if tickers else rs

        a = [r["chunk_id"] for r in keep(self.bm25.search(question, POOL))[:30]]
        b = [r["chunk_id"] for r in keep(self.dense.search(question, POOL))[:30]]
        return [self.by_id[cid] for cid, _ in rrf([a, b])[:k]]


def answer(retriever: Retriever, question: str) -> dict:
    chunks = retriever.search(question)
    passages = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)
    text = generate(PROMPT.format(passages=passages, question=question))
    return {"question": question, "answer": text, "retrieved": [c["chunk_id"] for c in chunks]}


if __name__ == "__main__":
    r = Retriever()
    for q in [
        "What supply chain risks does Apple describe?",
        "What is Apple's current stock price?",
        "How does Tesla describe risks from procuring battery cells from suppliers?",
    ]:
        out = answer(r, q)
        print("\nQ:", out["question"])
        print("A:", out["answer"])
        print("Retrieved:", out["retrieved"])
    from verify.citations import verify
    print("\n--- VERIFY ---")
    for q in ["What supply chain risks does Apple describe?",
              "How does Tesla describe risks from procuring battery cells from suppliers?"]:
        out = answer(r, q)
        v = verify(out["answer"], out["retrieved"], r.by_id)
        print(q, "->", v["unsupported"], "of", v["total"], "claims flagged")
        for c in v["claims"]:
            if c["problems"]:
                print("   ", c["problems"], "|", c["claim"][:80])

              