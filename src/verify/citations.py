import re

CITE = re.compile(r"\[([A-Z]+_\d{4}_[0-9A-Z]+_\d{3}(?:\s*,\s*[A-Z]+_\d{4}_[0-9A-Z]+_\d{3})*)\]")
NUM = re.compile(r"\$?\d[\d,]*\.?\d*%?")


def split_claims(answer: str) -> list[tuple[str, list[str]]]:
    """Split an answer into (claim_text, [cited_ids]) pieces."""
    claims, last = [], 0
    for m in CITE.finditer(answer):
        text = answer[last:m.start()].strip(" -\n")
        ids = [i.strip() for i in m.group(1).split(",")]
        if text:
            claims.append((text, ids))
        last = m.end()
    return claims


def verify(answer: str, retrieved: list[str], by_id: dict) -> dict:
    """Check citations. Returns per-claim results and a summary."""
    if answer.strip().lower().startswith("i don't know"):
        return {"abstained": True, "claims": [], "unsupported": 0, "total": 0}
    results = []
    for text, ids in split_claims(answer):
        problems = []
        for cid in ids:
            if cid not in by_id:
                problems.append(f"{cid}: does not exist")
            elif cid not in retrieved:
                problems.append(f"{cid}: not retrieved")
        source = " ".join(by_id[c]["text"] for c in ids if c in by_id).replace(",", "")
        for n in NUM.findall(text):
            if len(n.strip("$%,.")) >= 2 and n.replace(",", "") not in source:
                problems.append(f"number {n} not in cited text")
        results.append({"claim": text, "ids": ids, "problems": problems})
    bad = sum(1 for r in results if r["problems"])
    uncited = not results
    return {"abstained": False, "claims": results, "unsupported": bad + (1 if uncited else 0),
            "total": len(results) or 1}