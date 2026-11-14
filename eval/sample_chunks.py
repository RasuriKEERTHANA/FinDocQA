import json
import random
import sys
from pathlib import Path

# usage: python eval\sample_chunks.py MSFT 1A 3
ticker, item, n = sys.argv[1].upper(), sys.argv[2].upper(), int(sys.argv[3])
chunks = json.loads(Path("data/processed/all_chunks.json").read_text(encoding="utf-8"))
pool = [c for c in chunks if c["ticker"] == ticker and c["item"] == item]
for c in random.sample(pool, min(n, len(pool))):
    print("=" * 80)
    print(c["chunk_id"])
    print(c["text"])