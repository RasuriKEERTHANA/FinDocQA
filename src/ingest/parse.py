import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Sections we care about (Item number -> name)
ITEMS = {
    "1": "Business",
    "1A": "Risk Factors",
    "7": "MD&A",
    "7A": "Market Risk",
    "8": "Financial Statements",
}

def html_to_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text

def split_items(text: str) -> dict:
    # Find every "Item X." heading at the start of a line
    pattern = re.compile(r"^\s*item\s+(\d+[A-C]?)\s*[\.\:\-–—]", re.I | re.M)
    matches = [(m.group(1).upper(), m.start()) for m in pattern.finditer(text)]

    sections = {}
    for i, (item, start) in enumerate(matches):
        end = matches[i + 1][1] if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # keep the LONGEST match per item: the table of contents entry is tiny
        if item in ITEMS and len(body) > len(sections.get(item, "")):
            sections[item] = body
    return sections

if __name__ == "__main__":
    for path in sorted(Path("data/raw").glob("*_*.html")):
        ticker = path.stem.split("_")[0]
        sections = split_items(html_to_text(path))
        print(path.name, {k: f"{len(v):,}" for k, v in sections.items()})
        out = Path("data/processed") / f"{path.stem}.json"
        out.write_text(json.dumps(
            {"ticker": ticker, "file": path.name, "sections": sections}, indent=2),
            encoding="utf-8")