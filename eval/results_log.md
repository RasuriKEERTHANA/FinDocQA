2026-11-14  baseline v2, n=19 (no filter, equal-weight RRF, 400-word chunks)
BM25   hit@5 84%  MRR 0.747
Dense  hit@5 89%  MRR 0.719
Hybrid hit@5 95%  MRR 0.808
2026-11-16  + company filter, n=19
BM25+F   hit@5 84%   MRR 0.782
Dense+F  hit@5 89%   MRR 0.722
Hybrid+F hit@5 100%  MRR 0.789
# FinDocQA results log

Setup: 10 filings (AAPL, MSFT, NVDA, TSLA, JPM; 2 years each), 1,109 chunks
(400 words, 60 overlap). Embeddings: bge-small-en-v1.5. Metrics: hit-rate@5 and MRR.

## 2026-11-14  Baseline v1 (n=11)
BM25   hit@5 82%   MRR 0.766
Dense  hit@5 82%   MRR 0.671
Hybrid hit@5 91%   MRR 0.730
Note: questions written from phrases BM25 had surfaced, so BM25 was favored.

## 2026-11-14  Baseline v2 (n=19, no filter, equal-weight RRF)
BM25   hit@5 84%   MRR 0.747
Dense  hit@5 89%   MRR 0.719
Hybrid hit@5 95%   MRR 0.808
Note: q013-q020 written from passages I read, in my own words.

## 2026-11-16  + Company filter (n=19)
Change: detect company name in the question, keep only that company's chunks.
BM25+F   hit@5 84%    MRR 0.782
Dense+F  hit@5 89%    MRR 0.722
Hybrid+F hit@5 100%   MRR 0.789
Finding: filter helped hybrid by one question; BM25 and dense unchanged.
Caveat: every question names its company, and n=19 is small (1 question = ~5 points).

## 2026-11-16  Miss analysis (filtered, n=19)
5 misses total (hybrid: 0). BM25 missed q004, q005, q014. Dense missed q012, q019.
- 4 of 5 are near-misses: correct chunk ranked 6-13, just outside the top 5.
  -> candidates: reranker, weighted RRF.
- q004 and others: top results were valid answers from the other filing year,
  so labels are too strict (same text appears in FY2025 and FY2026).
  -> to do: widen labels to include equivalent chunks from both years.
- q005: BM25 matched common words ("prices", "tariffs"); the answer uses
  "designs, manufactures and markets" vs the question's "design, manufacture, market".
  -> candidate: stemming for BM25.
- BM25 and dense fail on different questions, which is why hybrid gets all 19.

## Next experiments
1. Weighted RRF (dense weight > BM25)
2. Cross-encoder reranker on top 20-30
3. Widen labels across filing years
4. Grow eval set to ~50 with a fixed dev/test split