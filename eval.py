"""Fill the report table: run your 5 test questions through all 3 modes (top-3 each).
Optional: add 'gold' (expected chunk_id substring) to get hit@3 per mode.
Usage: python eval.py
"""
from retrieval import MODES, retrieve
TESTS = [
    {"q": "What is MQTT used for?", "gold": None},
    {"q": "How do you unwind?", "gold": None},
    {"q": "What do you do when a submission date is close?", "gold": None},
    {"q": "Which cyber attacks did your paper cover?", "gold": None},
    {"q": "Which university course did you enjoy most?", "gold": None},
]
hits = {m: 0 for m in MODES}
labeled = 0
for t in TESTS:
    print(f"\n=== {t['q']}")
    for m in MODES:
        res = retrieve(t["q"], m, 3)
        print(f"  {m:13s}: " + " | ".join(f"{r['chunk_id']} ({r['score']})" for r in res))
        if t["gold"]:
            hits[m] += any(t["gold"] in r["chunk_id"] for r in res)
    labeled += bool(t["gold"])
if labeled:
    print("\nhit@3:", {m: f"{h}/{labeled}" for m, h in hits.items()})
