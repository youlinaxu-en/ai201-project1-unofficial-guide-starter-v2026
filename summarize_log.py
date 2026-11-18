#!/usr/bin/env python3
"""Summarize logs/requests.jsonl: counts, refusal rate, latency percentiles.

    python summarize_log.py [path]
"""
import json
import statistics
import sys
from pathlib import Path


def pct(values, p):
    if not values:
        return None
    values = sorted(values)
    k = max(0, min(len(values) - 1, round(p / 100 * (len(values) - 1))))
    return values[k]


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "logs/requests.jsonl")
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    asks = [r for r in rows if r.get("event") == "ask"]
    ok = [r for r in asks if r["status"] == 200]
    refused = [r for r in ok if r["refused"]]
    answered = [r for r in ok if not r["refused"]]

    print(f"requests: {len(asks)}  ok: {len(ok)}  errors: {len(asks) - len(ok)}")
    if ok:
        print(f"refused: {len(refused)} ({len(refused) / len(ok):.0%})  answered: {len(answered)}")
        print(f"mean best_distance: {statistics.mean(r['best_distance'] for r in ok):.3f}")
    for label, key, group in [
        ("total", "total_ms", ok),
        ("retrieval", "retrieval_ms", ok),
        ("generation", "generation_ms", answered),
    ]:
        vals = [r[key] for r in group if r.get(key) is not None]
        if vals:
            print(f"{label:11s} ms  p50={pct(vals, 50)}  p95={pct(vals, 95)}  max={max(vals)}")


if __name__ == "__main__":
    main()
