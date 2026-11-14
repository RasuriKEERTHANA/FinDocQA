
import json
import re
from pathlib import Path

ITEM_NAMES = {
    "1": "Business",
    "1A": "Risk Factors",
    "7": "MD&A",
    "7A": "Market Risk",
    "8": "Financial Statements",
}

CHUNK_WORDS = 400      # roughly 500-600 tokens
OVERLAP_WORDS = 60     # words repeated between neighbouring chunks
MIN_SECTION_CHARS = 2000   # skip pointer-only sections (e.g. JPM Item 7, NVDA Item 8)


def chunk_section(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS):
    """Split text into overlapping word windows, preferring paragraph breaks."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    words_per_para = [p.split() for p in paragraphs]

    chunks, current = [], []
    for words in words_per_para:
        # a single huge paragraph: split it by words
        while len(words) > size:
            if current:
                chunks.append(current)
                current = []
            chunks.append(words[:size])
            words = words[size - overlap:]
        if len(current) + len(words) > size and current:
            chunks.append(current)
            current = current[-overlap:]      # carry overlap into the next chunk
        current = current + words
    if current:
        chunks.append(current)
    return [" ".join(c) for c in chunks]


def chunk_filing(processed_path: Path) -> list[dict]:
    data = json.loads(processed_path.read_text(encoding="utf-8"))
    year = processed_path.stem.split("_")[1][:4]       # from report date
    out = []
    for item, text in data["sections"].items():
        if len(text) < MIN_SECTION_CHARS:              # skip pointer-only sections
            continue
        for n, chunk in enumerate(chunk_section(text), start=1):
            out.append({
                "chunk_id": f"{data['ticker']}_{year}_{item}_{n:03d}",
                "ticker": data["ticker"],
                "year": year,
                "item": item,
                "section": ITEM_NAMES[item],
                "table_heavy": item == "8",
                "text": chunk,
            })
    return out


if __name__ == "__main__":
    all_chunks = []
    for path in sorted(Path("data/processed").glob("*_20??-??-??.json")):
        filing_chunks = chunk_filing(path)
        print(f"{path.name}: {len(filing_chunks)} chunks")
        all_chunks += filing_chunks

    print(len(all_chunks), "chunks total")
    Path("data/processed/all_chunks.json").write_text(
        json.dumps(all_chunks, indent=2), encoding="utf-8"
    )
    print("Saved: data/processed/all_chunks.json")