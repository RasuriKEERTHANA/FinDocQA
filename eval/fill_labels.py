import json
from pathlib import Path

def norm(s: str) -> str:
    return s.lower().replace("’", "'").replace("“", '"').replace("”", '"')

chunks = json.loads(Path("data/processed/all_chunks.json").read_text(encoding="utf-8"))
path = Path("eval/questions.json")
questions = json.loads(path.read_text(encoding="utf-8"))

for q in questions:
    phrase = q.get("answer_phrase", "")
    if q["type"] == "unanswerable" or not phrase or phrase == "TODO":
        print(f"{q['id']}: skipped ({q['type']}, phrase={phrase or 'empty'})")
        continue
    q["relevant_chunks"] = [
        c["chunk_id"] for c in chunks
        if c["ticker"] == q["ticker"] and norm(phrase) in norm(c["text"])
    ]
    status = "OK" if q["relevant_chunks"] else "NO MATCH, fix phrase"
    print(f"{q['id']}: {len(q['relevant_chunks'])} chunks  {status}")

path.write_text(json.dumps(questions, indent=2), encoding="utf-8")