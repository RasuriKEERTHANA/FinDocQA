import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "src/retrieval")
sys.path.insert(0, "src/agent")
sys.path.insert(0, "src")

from answer import Retriever, answer
from verify.citations import verify

CACHE = Path("eval/answers_cache.json")
PAUSE = 4   # seconds between LLM calls, to respect free-tier limits


def abstained(text: str) -> bool:
    return text.strip().lower().startswith("i don't know")


if __name__ == "__main__":
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    questions = [q for q in questions if not q["question"].startswith("TODO")]
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}

    r = Retriever()
    for q in questions:
        if q["id"] in cache:
            continue
        try:
            out = answer(r, q["question"])
        except Exception as e:
            print(f"{q['id']}: FAILED ({type(e).__name__}), will retry next run")
            continue
        cache[q["id"]] = out
        CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        print(f"{q['id']}: done")
        time.sleep(PAUSE)

    unans = [q for q in questions if q["type"] == "unanswerable"]
    ans = [q for q in questions if q["type"] == "text" and q["relevant_chunks"]]
    unans = [q for q in unans if q["id"] in cache]
    ans = [q for q in ans if q["id"] in cache]

    right_abstain = sum(abstained(cache[q["id"]]["answer"]) for q in unans)
    wrong_abstain = sum(abstained(cache[q["id"]]["answer"]) for q in ans)

    flagged, total_answers, cited_ok = 0, 0, 0
    print("\n--- flagged answers ---")
    for q in ans:
        out = cache[q["id"]]
        if abstained(out["answer"]):
            continue
        v = verify(out["answer"], out["retrieved"], r.by_id)
        total_answers += 1
        if v["unsupported"]:
            flagged += 1
            print(q["id"], q["question"][:60])
            for c in v["claims"]:
                if c["problems"]:
                    print("    ", c["problems"], "|", c["claim"][:70])
        # did the answer cite at least one labeled-correct chunk?
        cited = {i for c in v["claims"] for i in c["ids"]}
        if cited & set(q["relevant_chunks"]):
            cited_ok += 1

    print("\n--- RESULTS ---")
    print(f"Abstention on unanswerable : {right_abstain}/{len(unans)}")
    print(f"Wrongful abstention        : {wrong_abstain}/{len(ans)}")
    print(f"Answers with flagged cites : {flagged}/{total_answers}")
    print(f"Cites a labeled chunk      : {cited_ok}/{total_answers}")