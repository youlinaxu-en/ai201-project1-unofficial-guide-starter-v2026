#!/usr/bin/env python3
"""Send a batch of questions to a running serve.py so the log has a real session.

    python send_questions.py [base_url]     (default http://localhost:5000)
"""
import json
import sys
import urllib.error
import urllib.request

QUESTIONS = [
    # in scope (campus_life corpus)
    "is the housing lottery random?",
    "how do I get a parking permit?",
    "what is the add/drop deadline?",
    "how hard is CS 210?",
    "what are the exams like in MATH 220?",
    "how much work is BIOL 160?",
    "can I take a class pass/fail?",
    "what is the printing quota?",
    "how do I request a transcript?",
    "what are the graduation requirements?",
    "how do I appeal a grade?",
    "how do dining dollars work?",
    # out of scope: should be refused by the gate
    "what is the best pizza topping in Antarctica?",
    "who won the 1998 world cup?",
    # bad input: should be a 400
    "",
]


def post(base, question):
    req = urllib.request.Request(
        f"{base}/ask",
        data=json.dumps({"question": question}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    for q in QUESTIONS:
        status, body = post(base, q)
        print(status, repr(q), "->", "refused" if body.get("refused") else body.get("error", "answered"))


if __name__ == "__main__":
    main()
