import json
import sys
from pathlib import Path

chunks = json.loads(Path("data/processed/all_chunks.json").read_text(encoding="utf-8"))
phrase = " ".join(sys.argv[1:]).lower()

for c in chunks:
    if phrase in c["text"].lower():
        i = c["text"].lower().index(phrase)
        print(c["chunk_id"], "...", c["text"][max(0, i - 80): i + 160].replace("\n", " "))