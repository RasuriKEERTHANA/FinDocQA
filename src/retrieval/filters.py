COMPANY_ALIASES = {
    "AAPL": ["apple", "aapl", "iphone"],
    "MSFT": ["microsoft", "msft", "azure"],
    "NVDA": ["nvidia", "nvda"],
    "TSLA": ["tesla", "tsla"],
    "JPM":  ["jpmorgan", "jp morgan", "jpmorganchase", "jpm", "chase"],
}

def detect_tickers(query: str) -> list[str]:
    """Return tickers mentioned in the query (empty list = no company named)."""
    q = query.lower()
    return [t for t, names in COMPANY_ALIASES.items() if any(n in q for n in names)]

if __name__ == "__main__":
    for q in ["What supply chain risks does Apple describe?",
              "Compare Tesla and NVIDIA R&D spend",
              "What are the main risks?"]:
        print(q, "->", detect_tickers(q))