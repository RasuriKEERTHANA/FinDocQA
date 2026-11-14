import json
import time
import requests
from pathlib import Path

# PUT YOUR REAL NAME AND EMAIL HERE
HEADERS = {"User-Agent": "Rasuri Keerthana r.keer2005@gmail.com"}
CACHE_DIR = Path("data/raw")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_json(url: str, cache_name: str | None = None) -> dict:
    """GET JSON from the SEC, with optional on-disk caching and a polite delay."""
    if cache_name:
        cache_file = CACHE_DIR / cache_name
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
    time.sleep(0.5)  # stay far below the SEC's 10 requests/second limit
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"{url} -> {resp.status_code}: {resp.text[:150]}")
    data = resp.json()
    if cache_name:
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    return data

CIKS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    "JPM":  "0000019617",
}

def get_cik(ticker: str) -> str:
    return CIKS[ticker.upper()]

def get_10k_urls(ticker: str, limit: int = 2) -> list[dict]:
    cik = get_cik(ticker)
    sub = fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json",
                     cache_name=f"submissions_{ticker.upper()}.json")

    # the "recent" block first, then any older archive files
    blocks = [sub["filings"]["recent"]]
    results = []

    def collect(block):
        for i, form in enumerate(block["form"]):
            if form == "10-K":
                acc = block["accessionNumber"][i].replace("-", "")
                doc = block["primaryDocument"][i]
                results.append({
                    "ticker": ticker.upper(),
                    "filing_date": block["filingDate"][i],
                    "report_date": block["reportDate"][i],
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}",
                })
                if len(results) == limit:
                    return True
        return False

    if collect(blocks[0]):
        return results

    for f in sub["filings"].get("files", []):
        older = fetch_json(f"https://data.sec.gov/submissions/{f['name']}",
                           cache_name=f"submissions_{ticker.upper()}_{f['name']}")
        if collect(older):
            break
    return results

def download(filing: dict) -> Path:
    out = CACHE_DIR / f"{filing['ticker']}_{filing['report_date']}.html"
    if out.exists():
        return out
    time.sleep(0.5)
    resp = requests.get(filing["url"], headers=HEADERS, timeout=60)
    resp.raise_for_status()
    out.write_text(resp.text, encoding="utf-8")
    return out

if __name__ == "__main__":
    for ticker in ["AAPL", "MSFT", "NVDA", "TSLA", "JPM"]:
        for filing in get_10k_urls(ticker, limit=2):
            print(ticker, filing["report_date"], "->", download(filing))