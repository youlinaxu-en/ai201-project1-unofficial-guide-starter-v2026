#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

Logging (Unit 9): every /ask writes one JSON line to logs/requests.jsonl (and
stdout) with request_id, status, refused, best_distance, sources, and timing
split into retrieval_ms / generation_ms / total_ms. summarize_log.py turns
that file into the numbers.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

import config

app = Flask(__name__)

# Structured log: one JSON object per line, appended to logs/requests.jsonl.
# logs/ is NOT gitignored on purpose -- a real session's log is the run record.
LOG_PATH = Path(os.getenv("AI201_LOG_PATH", "logs/requests.jsonl"))


def log_event(**fields):
    """Append one JSON line to the log file and echo it to stdout."""
    record = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **fields}
    line = json.dumps(record, ensure_ascii=False)
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:  # logging must never take the service down
        print(json.dumps({"event": "log_write_failed", "error": str(exc)}), flush=True)


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    request_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        log_event(
            event="ask", request_id=request_id, status=400, error="empty_question",
            total_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    marks = {}

    def on_gate(_decision):
        # Fires right after retrieval + gate, before the model call.
        marks["retrieval_ms"] = round((time.perf_counter() - started) * 1000, 1)

    try:
        outcome = ask_pipeline(question, corpus=config.CORPUS, on_gate=on_gate)
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        log_event(
            event="ask", request_id=request_id, status=500,
            question=question, error=f"{type(exc).__name__}: {exc}",
            total_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    retrieval_ms = marks.get("retrieval_ms")
    log_event(
        event="ask",
        request_id=request_id,
        status=200,
        corpus=config.CORPUS,
        question=question,
        refused=outcome["refused"],
        best_distance=round(outcome["best_distance"], 4),
        threshold=outcome["threshold"],
        sources=outcome["sources"],
        answer_chars=len(outcome["answer"]),
        retrieval_ms=retrieval_ms,
        generation_ms=(
            None if outcome["refused"] or retrieval_ms is None
            else round(total_ms - retrieval_ms, 1)
        ),
        total_ms=total_ms,
    )

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
