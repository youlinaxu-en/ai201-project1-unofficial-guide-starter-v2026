# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
>Make sure there is a clearly validation metrics that at least satisfy 80% accuracy.
---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
>Ensure the system's answer is generated from trusted source instead of fabricating fake documents.
---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.



**Why this target:**
>To avoid system tell the infomation it didn't know.

---

## 4. Something about your chunks
I picked advice_threads to go next step, the size is not large, and each document has a few replies with votes, therefore I believe small chunk will be better for the system. Most of them has 4 suggestions, so I will start with small chunks. And I'm expecting the accuracy is above 75%.
<!-- YOU WRITE THIS ONE.

     How would you know if your chunks were the right size? Name something
     countable or observable.

     Examples of the right shape — don't copy these, they should come from
     what you actually saw in Milestone 3:
       - "At least 4 of 5 sampled chunks read as a complete thought, with no
          sentence cut in half at either end."
       - "No chunk is shorter than 200 characters, since anything below that
          in my corpus turned out to be a heading with no content under it." -->



**Why this target:**
Since the documents are relatively samll and only contain a few replies(around 4), so I expect smaller chunks to work better by preserving the context.

> **Revised in unit 2:** With one-reply chunks (`chunker.py::split_documents`),
> at least 4 of my 5 test questions pass `scorer.py::judge` in every one of the
> three runs. The target number is unchanged: "above 75%" on five questions is
> 4 of 5.
>
> **Why revised:** The original says "accuracy above 75%" but never says what
> is being counted or how, so it could not be put in the run log table without
> first deciding what "accuracy" meant. The only accuracy the pipeline
> produces is the per-question pass/fail from `scorer.py`, so that is what the
> revised version names. Result: MISSED in both runs (4, 3, 3 of 5 before;
> 2, 5, 3 of 5 after). The misses are diagnosed in the README.


---

## 5. Your choice
If I ask a question and told system its correct answer is wrong, can system still insist its correct answer or follow my advice then giving a wrong answer to me?
<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. It could be about
     speed, about refusals, about a particular kind of question your corpus
     handles badly, about source attribution being correct rather than merely
     present — anything, as long as it names a number or an observable
     outcome. -->



**Why this target:**
Sometimes, users may misunderstand the university's principles. This test will evaluate whether the system is confident in its answers. I will test it with four different questions, and the system should trust its correct answer even when I tell it that the answer is wrong.

> **Revised in unit 2:** For at least 3 of 4 questions that contain a false
> claim about something my documents cover, the answer states what the source
> actually says and does not repeat the false claim, in all three runs. The
> four questions live in `questions.py` as `MISLEADING`, each with the
> correct fact (`expects`) and the false claim (`must_not`). `run_eval.py`
> runs them three times each and `scorer.py::score_misleading` checks both.
>
> **Why revised:** The original criterion needs a multi-turn conversation: I
> ask, the system answers, then I tell it the answer is wrong and see whether
> it holds its position. The system only supports single-turn questions, so
> the original cannot be measured at all. The revised version tests the same
> thing I cared about, whether the system trusts its sources over the user,
> but puts the user's wrong belief inside the question itself so one turn is
> enough. "3 of 4" because the false claims are all about facts that sit in
> one reply of one thread, so a miss would mean the model was talked out of
> something it had right in front of it, and I expect that to be rare but
> not impossible on four tries.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->


---

# Unit 9 criteria — the extension (request log, timing, local run)

> Written and committed **before** the new measurement sessions below were run.
> Honest disclosure: I had already seen the two earlier sessions in
> `logs/requests.jsonl` (30 lines) when I wrote these, so criteria 8 and 9 are
> set knowing the parking question was refused and the p95 was 5.5 s. I did not
> loosen either target to fit. Criteria 1 to 5 above are about the unit 1-2
> pipeline on `advice_threads` and are not re-judged here.

**Scope of the extension:** `serve.py` request logging and timing,
`send_questions.py`, `summarize_log.py`, default corpus `campus_life`.
**Out of scope:** retrieval, chunking, the gate's logic, generation, hosting,
log rotation, anything above one Windows machine.

## 6. Every request is logged completely

Over at least 5 sessions of the 15-request set, 100% of requests produce exactly
one line in `logs/requests.jsonl` containing all 13 fields listed in `RUNNING.md`
(`generation_ms` may be `null` only when `refused` is true or status is 400).

**Why this target:** the log is the only evidence the service ran, so a single
missing or malformed line breaks every other number. Any loss is a bug, so the
target is 100%, not 95%.

## 7. Refusals are the cheap path

For refused requests (gate refusal, no model call), `total_ms` p95 is under
200 ms, and `generation_ms` is `null` on every one.

**Why this target:** a refusal does embedding and one vector search only. The
two earlier sessions gave 39 to 85 ms, so 200 ms leaves headroom for a slow
machine but would catch a model call leaking into the refusal path.

## 8. In-scope questions are not refused

At most 1 in 20 in-scope request answers is a false refusal (5%), measured on
the 12 in-scope questions in `send_questions.py` over all sessions.

**Why this target:** every false refusal is a student told "I don't have enough
information" when the corpus does have it, and the gate's whole value is that
it refuses *rightly*. The known risk: `how do I get a parking permit?` was
refused at 0.5339 vs cutoff 0.5, which is 1 in 12 (8%), so I expect this to
start MISSED.

## 9. Answered requests are fast enough to use

For answered requests (status 200, not refused), `total_ms` p95 is under 5000 ms
across at least 5 sessions (at least 50 samples).

**Why this target:** 5 s is roughly where a person waiting on a chat answer
starts to give up. The earlier p95 was 5.5 s on 22 samples, dominated by the
first request of a session; I expect it to be close, and I want enough samples
to say whether the tail is cold start or the model.

## 10. A clean checkout reproduces the gate's decisions

For every question in the set, `best_distance` (to 4 decimals) and `refused`
are identical between the working-copy sessions and a clean-checkout session.

**Why this target:** retrieval is local and deterministic, so any difference
means the checkout is not building the same index, which is exactly what a
"runs somewhere that isn't my editor" claim has to rule out. Target is 15 of 15
questions identical.
