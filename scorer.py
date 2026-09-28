"""
Decides whether an answer was right. The starter left this out on purpose.

`run_eval.py` looks for this file and calls

    judge(question, expects, answer, results) -> bool

once per run of each question. When it returns True the run log says "pass",
False says "fail".

What "right" means here, in order:

  1. The answer is not the gate's refusal. A refused in-scope question is a
     fail, whatever else is true.
  2. The answer names at least one of the source files retrieval handed the
     model (criterion 2 in criteria.md). Turn this off with REQUIRE_SOURCE if
     you decide attribution should be scored separately from correctness.
  3. The answer contains the `expects` phrase from questions.py. Exact match
     of the whole phrase passes outright. Otherwise the phrase is reduced to
     its content words (stopwords dropped, light stemming so "reduce" and
     "reducing" count as the same word) and at least MIN_WORD_FRACTION of
     those words have to appear in the answer.

`score()` returns the full breakdown behind the bool so you can see which of
the three checks failed and which expected words were missing. That is what
makes a fail diagnosable rather than just a red cell.

Two ways to run it by hand, neither of which costs an API call:

    python scorer.py                          show the content words each
                                              question will be judged on
    python scorer.py results/run_X.md         re-score an existing run log
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REFUSAL = "I don't have enough information about that."

# Should an answer that gets the content right but cites no source count as
# wrong? criteria.md criterion 2 says every answer names a source, so yes.
REQUIRE_SOURCE = True

# Fraction of the expected content words that must appear in the answer when
# the whole phrase is not present verbatim. 0.5 means "at least half".
MIN_WORD_FRACTION = 0.5

# Words that carry no meaning for matching. Deliberately includes hedges and
# quantity words ("lot", "sometimes") because they say nothing about the
# answer's content. "yes" and "no" are NOT in here: for a yes/no question they
# are the answer.
STOPWORDS = {
    "a", "an", "the", "is", "it", "its", "of", "to", "and", "but", "or", "in",
    "on", "for", "with", "you", "your", "my", "i", "me", "we", "our", "can",
    "need", "lot", "some", "sometimes", "very", "much", "many", "more", "most",
    "if", "then", "than", "that", "this", "these", "those", "be", "are", "was",
    "were", "do", "does", "did", "will", "should", "would", "could", "have",
    "has", "had", "also", "from", "by", "at", "as", "so", "not", "they",
    "them", "their", "there", "here", "what", "which", "who", "how", "when",
    "where", "really", "actually", "kind", "thing", "things", "just", "get",
    "got", "going", "go", "about", "into", "out", "up", "down", "any", "all",
}

_SUFFIXES = ("ing", "edly", "ed", "es", "ly", "s", "e")


# ─── Text helpers ────────────────────────────────────────────────────────────


def normalise(text: str) -> str:
    """Lowercase, punctuation to spaces, single spaces."""
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stem(word: str) -> str:
    """Very light stemming: strip one common suffix if a root of 3+ letters is left."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def content_words(text: str) -> list[str]:
    """The stems worth matching on, in order, without duplicates."""
    seen: list[str] = []
    for word in normalise(text).split():
        word = word.strip("'")
        if len(word) < 2 or word in STOPWORDS:
            continue
        s = stem(word)
        if s not in seen:
            seen.append(s)
    return seen


def _same_word(a: str, b: str) -> bool:
    """Stems equal, or long words sharing their first five letters
    ("advisor" / "adviser", "programme" / "program")."""
    if a == b:
        return True
    return len(a) >= 6 and len(b) >= 6 and a[:5] == b[:5]


def phrase_match(expects: str, text: str) -> tuple[bool, list[str], list[str], float]:
    """
    Does `text` contain what `expects` says?

    Returns (matched, found_words, missing_words, fraction).
    """
    if not expects.strip():
        # Nothing to check against. Don't fail a question for a blank expects.
        return True, [], [], 1.0

    if normalise(expects) in normalise(text):
        words = content_words(expects)
        return True, words, [], 1.0

    wanted = content_words(expects)
    present = content_words(text)
    found = [w for w in wanted if any(_same_word(w, p) for p in present)]
    missing = [w for w in wanted if w not in found]
    fraction = len(found) / len(wanted) if wanted else 1.0
    return fraction >= MIN_WORD_FRACTION, found, missing, fraction


def is_refusal(answer: str) -> bool:
    return normalise(answer).startswith(normalise(REFUSAL))


# Words that, within PREMISE_WINDOW words before the false claim, mean the
# answer is denying it rather than repeating it. "the highest tier is NOT the
# best" should not count as agreeing with "highest tier is the best".
PREMISE_NEGATIONS = {
    "not", "no", "never", "isn't", "aren't", "don't", "doesn't", "didn't",
    "won't", "wouldn't", "can't", "cannot", "rather", "instead", "unlike",
    "incorrect", "wrong", "false", "actually", "however", "although",
    "contrary", "mistaken", "misconception", "myth",
    # comparatives: "far more than a couple of minutes" is a denial too
    "than", "beyond",
}
PREMISE_WINDOW = 8


def repeats_premise(answer: str, must_not: str) -> bool:
    """
    Does the answer go along with the false claim in the question?

    True when `must_not` appears in the answer with no negation word in the
    PREMISE_WINDOW words before it. A negated mention ("it is not automatic")
    is the model correcting the user, which is what criterion 5 wants.
    """
    if not must_not.strip():
        return False
    words = normalise(answer).split()
    target = normalise(must_not).split()
    if not target:
        return False
    for i in range(len(words) - len(target) + 1):
        window = words[i : i + len(target)]
        # substring on the first word so "automatic" catches "automatically"
        if window[0].startswith(target[0]) and window[1:] == target[1:]:
            before = words[max(0, i - PREMISE_WINDOW) : i]
            if not any(w in PREMISE_NEGATIONS for w in before):
                return True
    return False


def _source_names(results) -> list[str]:
    names = []
    for r in results or []:
        name = r if isinstance(r, str) else getattr(r, "source", "")
        if name and name not in names:
            names.append(name)
    return names


def names_source(answer: str, results) -> bool:
    """Does the answer mention any retrieved source file, with or without .txt?"""
    low = answer.lower()
    for name in _source_names(results):
        base = Path(name).stem.lower()
        if name.lower() in low or (len(base) >= 6 and base in low):
            return True
    return False


# ─── The verdict ─────────────────────────────────────────────────────────────


@dataclass
class Verdict:
    passed: bool
    refused: bool
    source_named: bool
    expects_matched: bool
    fraction: float
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    # Did any retrieved chunk itself contain the expected answer? This is the
    # evidence for criterion 1 (retrieval), separate from whether the model
    # then wrote it down. None when no chunk text was available.
    chunk_has_answer: bool | None = None
    # Criterion 5 only: did the answer repeat the false claim from the
    # question? None for ordinary questions, which have no false claim.
    premise_repeated: bool | None = None

    @property
    def reason(self) -> str:
        if self.refused:
            return "refused by the gate"
        parts = []
        if REQUIRE_SOURCE and not self.source_named:
            parts.append("no source named")
        if not self.expects_matched:
            parts.append(
                f"expects {self.fraction:.0%} matched, missing: {', '.join(self.missing) or '-'}"
            )
        if self.premise_repeated:
            parts.append("repeated the false claim from the question")
        return "; ".join(parts) if parts else f"ok ({self.fraction:.0%} of expected words)"


def score(question: str, expects: str, answer: str, results) -> Verdict:
    """The full breakdown. `judge` is this collapsed to one bool."""
    refused = is_refusal(answer)
    source_named = names_source(answer, results)
    matched, found, missing, fraction = phrase_match(expects, answer)

    chunk_has_answer: bool | None = None
    texts = [getattr(r, "text", None) for r in results or []]
    texts = [t for t in texts if t]
    if texts:
        chunk_has_answer = any(phrase_match(expects, t)[0] for t in texts)

    passed = (
        not refused
        and matched
        and (source_named or not REQUIRE_SOURCE)
    )
    return Verdict(
        passed=passed,
        refused=refused,
        source_named=source_named,
        expects_matched=matched,
        fraction=fraction,
        found=found,
        missing=missing,
        chunk_has_answer=chunk_has_answer,
    )


def judge(question: str, expects: str, answer: str, results) -> bool:
    """The function run_eval.py calls. True means the answer was right."""
    return score(question, expects, answer, results).passed


def score_misleading(question: str, expects: str, must_not: str, answer: str, results) -> Verdict:
    """
    Criterion 5 (revised in unit 2): the question contains a false claim.

    Passes when the ordinary checks pass (not refused, source named, `expects`
    present) AND the answer does not repeat the false claim in `must_not`.
    """
    v = score(question, expects, answer, results)
    v.premise_repeated = repeats_premise(answer, must_not)
    v.passed = v.passed and not v.premise_repeated
    return v


def judge_misleading(question: str, expects: str, must_not: str, answer: str, results) -> bool:
    """Criterion 5 collapsed to one bool, for run_eval.py."""
    return score_misleading(question, expects, must_not, answer, results).passed


# ─── Command line: inspect, or re-score a saved run log ──────────────────────


def _show_expectations() -> None:
    import questions as qs

    print("What each question will be judged on\n")
    for item in qs.answered():
        words = content_words(item.get("expects", ""))
        need = math.ceil(len(words) * MIN_WORD_FRACTION) if words else 0
        print(f"Q: {item['question'].strip()}")
        print(f"   expects: {item.get('expects', '')!r}")
        print(f"   content words ({len(words)}): {', '.join(words)}")
        print(f"   needs the whole phrase, or at least {int(need)} of those words")
        print(f"   plus a named source: {'yes' if REQUIRE_SOURCE else 'no'}\n")

    misleading = getattr(qs, "misleading", lambda: [])()
    if misleading:
        print("False-premise questions (criterion 5) — same checks, plus the false claim must not be repeated\n")
        for item in misleading:
            words = content_words(item.get("expects", ""))
            need = math.ceil(len(words) * MIN_WORD_FRACTION) if words else 0
            print(f"Q: {item['question'].strip()}")
            print(f"   expects:  {item.get('expects', '')!r}")
            print(f"   must_not: {item.get('must_not', '')!r}  (unless negated within {PREMISE_WINDOW} words)")
            print(f"   content words ({len(words)}): {', '.join(words)}")
            print(f"   needs the whole phrase, or at least {int(need)} of those words\n")


_HEADER = re.compile(r"^### (.*) — run (\d+)\s*$")
_SOURCES = re.compile(r"^- Sources retrieved: (.*)$")


def _parse_log(path: Path) -> list[dict]:
    """Pull (question, run, sources, answer) out of a run_eval.py results file."""
    entries: list[dict] = []
    current: dict | None = None
    in_code = False
    buf: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if in_code:
            if line.strip() == "```":
                in_code = False
                if current is not None:
                    current["answer"] = "\n".join(buf).strip()
                    entries.append(current)
                    current = None
            else:
                buf.append(line)
            continue

        m = _HEADER.match(line)
        if m:
            current = {"question": m.group(1).strip(), "run": int(m.group(2)), "sources": []}
            continue
        if current is not None:
            m = _SOURCES.match(line)
            if m:
                srcs = m.group(1).strip()
                current["sources"] = [] if srcs == "none" else [s.strip() for s in srcs.split(",")]
                continue
            if line.strip() == "```":
                in_code = True
                buf = []
    return entries


def _rescore(path: Path) -> None:
    import questions as qs

    expects_for = {q["question"].strip(): q.get("expects", "") for q in qs.answered()}
    misleading_for = {
        q["question"].strip(): q
        for q in getattr(qs, "misleading", lambda: [])()
    }
    entries = _parse_log(path)
    if not entries:
        print(f"No answers found in {path}. Is it a run_eval.py results file?")
        sys.exit(1)

    print(f"Re-scoring {path} with scorer.py::judge\n")
    by_question: dict[str, list[bool]] = {}
    sources_ok: dict[str, list[bool]] = {}
    premise_ok: dict[str, list[bool]] = {}
    for e in entries:
        if e["question"] in misleading_for:
            item = misleading_for[e["question"]]
            v = score_misleading(
                e["question"], item.get("expects", ""), item.get("must_not", ""),
                e["answer"], e["sources"],
            )
            premise_ok.setdefault(e["question"], []).append(v.passed)
        else:
            expects = expects_for.get(e["question"])
            if expects is None:
                print(f"  (skipping '{e['question']}': not in questions.py)")
                continue
            v = score(e["question"], expects, e["answer"], e["sources"])
            by_question.setdefault(e["question"], []).append(v.passed)
            sources_ok.setdefault(e["question"], []).append(v.source_named)
        mark = "pass" if v.passed else "FAIL"
        print(f"{mark}  run {e['run']}  {e['question']}")
        print(f"       {v.reason}")

    n_runs = max((len(r) for r in by_question.values()), default=0)
    print("\n| Question | " + " | ".join(f"Run {i}" for i in range(1, n_runs + 1)) + " |")
    print("|---|" + "|".join(["---"] * n_runs) + "|")
    for q, runs in by_question.items():
        cells = " | ".join("pass" if p else "fail" for p in runs)
        print(f"| {q} | {cells} |")

    print("\nPer run, how many of the questions passed (criterion 1 row material):")
    for i in range(n_runs):
        passed = sum(1 for runs in by_question.values() if len(runs) > i and runs[i])
        print(f"  run {i + 1}: {passed} of {len(by_question)}")
    print("Per run, how many answers named a source (criterion 2 row material):")
    for i in range(n_runs):
        named = sum(1 for runs in sources_ok.values() if len(runs) > i and runs[i])
        print(f"  run {i + 1}: {named} of {len(sources_ok)}")
    if premise_ok:
        n_m = max(len(r) for r in premise_ok.values())
        print("Per run, how many false-premise answers followed the source (criterion 5 row material):")
        for i in range(n_m):
            held = sum(1 for runs in premise_ok.values() if len(runs) > i and runs[i])
            print(f"  run {i + 1}: {held} of {len(premise_ok)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        _rescore(Path(sys.argv[1]))
    else:
        _show_expectations()
