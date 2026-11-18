# The Unofficial Guide

youlinaxu-en · corpus: `advice_threads`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a small retrieval-augmented question answering system over the `advice_threads` corpus: 23 forum-style threads where several students reply to one practical question about campus life, such as whether a bike is worth it for a 20-minute commute, which meal plan tier to buy, how hard it is to change major in second year, or what first-generation students should know. Each thread is split into its individual replies, the replies are embedded locally with `all-MiniLM-L6-v2` and stored in Chroma, and a new question pulls back the six closest replies by distance. If even the closest reply is further away than the relevance cutoff, the system answers "I don't have enough information about that" instead of guessing; otherwise Gemini writes a short answer from those replies and names the thread file it came from. It does best on "should I / is it worth it / which one" questions whose answer is an opinion sitting in one reply, and it does worse when a question depends on campus-specific names or nicknames that the documents only use in passing, because nothing in the pipeline knows those refer to the same thing the question is asking about.

## Chunking Strategy

**Chunk size:** one reply per chunk, with the thread's `THREAD: ...` title line prepended. On this corpus that comes out at 104 to 253 characters (174 on average), 75 chunks from 23 threads. The `CHUNK_SIZE = 800` in `config.py` is no longer read by `split_documents`; only `fallback_split` uses it.

**Overlap:** 0 characters between neighbouring replies. Instead, every chunk from the same thread repeats the title line, which does the job overlap normally does: it carries the question into each piece so the piece still makes sense on its own.

**Why these numbers.** When I read the documents in Milestone 1, every file had the same shape: one `THREAD: <question>` line, then two to five replies separated by `--- reply N (votes) ---` markers. A whole thread is 317 to 793 characters, and each reply is one to three sentences holding one self-contained opinion, often disagreeing with the reply above it. That is why I wrote in `criteria.md` that I expected small chunks to work better here.

The starter's default numbers did badly on this shape. With an 800-character window nothing gets cut, so every thread came back as one chunk with all the disagreeing replies mixed together (the meal-plan thread's "get the middle tier", "the highest tier only makes sense if you eat three meals a day in the halls" and "you can only change it once" all land in the same chunk). Worse, the window steps forward by 680 characters (800 minus the 120 overlap) without checking whether anything is left, so the three threads longer than 680 characters also produced a duplicate tail fragment; the shortest was 2 characters long. That gave 26 chunks, 3 of them junk. A fixed window and a useful boundary were never going to line up here, but the reply markers already are the useful boundary, so I split on those instead.

The title matters more than it looks. A bare reply like `16 is the answer.` (thread_laptop_specs.txt#2) or `The library being open until 2am is a trap.` means nothing without the question it answers, so a question about laptops would never land on it. Prepending the title is what lets a one-line reply embed near the question it answers.

I did not change the strategy partway through, but running `app.py chunks` showed me its cost. Sample Chunk 5 below is on the sleep thread and does not actually answer the question about sleep. With one reply per chunk there is nothing else in the chunk to pull it back toward the topic, so a tangential reply can be retrieved on the strength of its title alone. That is the trade I made for keeping each opinion separate, and it is the first thing I would look at if criterion 1 misses in unit 2.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

======================================================================
Chunk 1  |  source: thread_bike_commute.txt#0  |  produced by: chunker.py::split_documents
======================================================================
THREAD: Is a bike worth it for a 20 minute walk commute?
Yeah. Cuts an 18 minute walk to about 6. The thing nobody mentions is storage — covered bike parking exists at three buildings and is full by 9am at all three.

======================================================================
Chunk 2  |  source: thread_first_gen.txt#1  |  produced by: chunker.py::split_documents
======================================================================
THREAD: Anything specific for first-generation students?
The thing I'd say: the unwritten rules are the hard part, not the coursework. Ask about the unwritten rules explicitly. People are happy to explain them and nobody volunteers them.

======================================================================
Chunk 3  |  source: thread_laptop_specs.txt#2  |  produced by: chunker.py::split_documents
======================================================================
THREAD: How much laptop do I actually need for CS courses?
I did two years on an 8GB machine and it was fine until the last project, at which point it very much wasn't. 16 is the answer.

======================================================================
Chunk 4  |  source: thread_parking.txt#1  |  produced by: chunker.py::split_documents
======================================================================
THREAD: Worth getting a parking permit?
Street parking on Verrill is legal and free and unmarked, which is why half the upper years do it.

======================================================================
Chunk 5  |  source: thread_sleep_schedule.txt#1  |  produced by: chunker.py::split_documents
======================================================================
THREAD: Everyone says fix your sleep. Does it actually matter?
The library being open until 2am is a trap. It's a resource, not a schedule.
>Chunk 5 was under that sleep_schedult file, but not directly related to the question.

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**
what kind of meal plan should I buy

**Answer:**
Based on the provided documents, the meal plan you should buy depends entirely on whether your building has a kitchen. If your building has a kitchen (like Fenwick, which has kitchenettes), you should go down a tier and cook two or three nights, while everywhere else you should get the middle tier.
```
```

**My relevance cutoff: 0.5**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus-advice_threads | Best distance |

>-- in scope --
0.398  should i take a bike if it's going to take me 20 mins  -> thread_bike_commute.txt#2
0.161  is it hard to change my major in the second year  -> thread_changing_major.txt#2
0.336  Anything specific for first-generation students?  -> thread_first_gen.txt#1
0.319  Is it matter to fix my sleep  -> thread_sleep_schedule.txt#2
0.299  which kind of meal plan is much better  -> thread_meal_plan_tier.txt#2
>-- out of scope --
0.899  What is the capital of Mongolia?
0.905  How do I change the oil in a diesel engine?
0.898  Who won the 1994 World Cup?
0.819  What is the recommended dosage of ibuprofen for a headache?
0.861  How do I write a for loop in Rust?

## How I Used AI

>1. Setting the relevance cutoff. I asked where my five test questions lived and what the best distance was for each. Claude ran retrieval on the five in `QUESTIONS` and the five in `OUT_OF_SCOPE` and gave back the table that is now under "My relevance cutoff": in-scope best distances from 0.161 to 0.398, out-of-scope from 0.819 to 0.905. Its recommendation was to leave `THRESHOLD` at the default 0.6, since that already sits inside the gap. I did not take that as-is. I set the cutoff at 0.5 instead, so it sits closer to the in-scope group than to the out-of-scope one, and a question that is only loosely about my corpus is more likely to be refused than half-answered. Around the same time I asked where to change top-k and moved it from 5 to 6 in `config.py`, so a whole five-reply thread plus one neighbour can come back for a single question.

>2. Unit 2, reading the run log. I asked Claude why the meal plan row in the false-premise table said fail in runs 1 and 3 when the answers looked right to me. It read `scorer.py`, worked out the content words the `expects` phrase reduces to (depend, entire, whether, build, kitchen) and scored the three answers by hand: 1, 4 and 2 of 5 words. That showed the fails were my phrase, not the model agreeing with the false claim, and it is why the meal plan `expects` in `questions.MISLEADING` is now keyed to the "three meals a day" reply. Re-scoring alone would have hidden the change, so I had it re-run the whole eval instead.

>3. Unit 2, spotting the pattern in the misses. I asked Claude to fill in the run log, verdicts and diagnoses from the new log. It ran `app.py retrieve` on all five questions for criterion 1, ran `python scorer.py <log>` to get the missing words per fail, and pointed out that every criterion 4 miss had the right thread fully retrieved and the right facts in the answer, and differed from my `expects` only in wording. The diagnosis section above is that finding in my words. It also proposed the prompt change in `generate.py`, ran the after eval, and reported that the bike question got worse rather than smoothing it over. The "backfired" reading of the bike result came from its re-score output, which lists the missing words per run.

>What I kept and what I changed: the "at least 4 of 5 per run" reading of criterion 4 was Claude's suggestion and I accepted it because it is the strictest reading the pipeline can measure. I kept the prompt change in `generate.py` even though it did not fix criterion 4, because the changing-major answers are better for a reader and the README has to show a fix I actually tried. I did not let it re-key the `expects` phrases in the same unit, so the before and after tables are scored the same way. Two evals were interrupted by Gemini 503 errors and re-run from the start; no partial logs were kept.


<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

All numbers below are from `results/run_2026-09-27_2238_before.md`, produced
by `python run_eval.py --label before --pause 4` on 2026-09-27 with top-k 6.

Both run logs say cutoff 0.6 because `config.py` still had the starter default
when they ran; unit 1 above says 0.5, which is what I meant. I have since set
`THRESHOLD = 0.5` in `config.py`. The logs are still valid for 0.5: every
in-scope best distance is below 0.44 and every out-of-scope one is above 0.81,
so the gate makes the same decision on all fifteen questions at either value.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. One-reply chunks give end-to-end accuracy above 75% (read as: at least 4 of 5 questions pass the scorer in every run) | 4 of 5 | 4 of 5 | 3 of 5 | 3 of 5 | MISSED |
| 5. Answer follows the source, not a false claim in the question (revised) | 3 of 4 | 4 of 4 | 4 of 4 | 4 of 4 | MET |

**Criterion 1 — real output.** Retrieval is deterministic, so one pass is the
whole measurement and the same count goes in all three columns. Produced by
`python app.py retrieve "..."` (`app.py::cmd_retrieve`, which calls
`store.py::search`). For every one of the five questions, every reply of the
matching thread came back inside the top 6, so the chunk holding the answer
was always retrieved. The two questions that later failed criterion 4 are
shown here to make the point that their misses were not retrieval misses:

```
Question: is it hard to change my major in the second year

#   distance   source                           preview
1   0.1612     thread_changing_major.txt        THREAD: How hard is it to change major in second yea...
2   0.2100     thread_changing_major.txt        THREAD: How hard is it to change major in second yea...
3   0.3059     thread_changing_major.txt        THREAD: How hard is it to change major in second yea...
4   0.5101     thread_transfer_credits.txt      THREAD: Do transfer credits actually count toward th...
5   0.5798     thread_transfer_credits.txt      THREAD: Do transfer credits actually count toward th...
6   0.6241     thread_pass_fail.txt             THREAD: When should you actually use the pass/fail o...

Question: which kind of meal plan is much better

#   distance   source                           preview
1   0.2988     thread_meal_plan_tier.txt        THREAD: Which meal plan tier is right? Remember you ...
2   0.3309     thread_meal_plan_tier.txt        THREAD: Which meal plan tier is right? The highest t...
3   0.4228     thread_meal_plan_tier.txt        THREAD: Which meal plan tier is right? Depends entir...
4   0.4410     thread_meal_plan_tier.txt        THREAD: Which meal plan tier is right? Declining bal...
5   0.7739     thread_bike_commute.txt          THREAD: Is a bike worth it for a 20 minute walk comm...
6   0.7977     thread_bike_commute.txt          THREAD: Is a bike worth it for a 20 minute walk comm...
```

The changing-major thread has three replies and all three are the top three
results. The meal plan thread has four replies and all four are the top four.

**Criterion 2 — real output.** Scored by `scorer.py::names_source`, which
looks for any retrieved filename (with or without `.txt`) in the answer.
Re-scoring the log with `python scorer.py results/run_2026-09-27_2238_before.md`
prints "how many answers named a source: run 1: 5 of 5, run 2: 5 of 5,
run 3: 5 of 5". One of the 15 answers, from `generate.py::answer_from_chunks`:

```
Administratively, changing your major is trivial as it just requires a form, but whether it is difficult depends on whether your previously taken credits map onto the new requirements. (Source: thread_changing_major.txt)
```

**Criterion 3 — real output.** Produced by `run_eval.py::check_out_of_scope`
with `gate.py::check` at cutoff 0.6. One deterministic pass, so the same 5 of 5
goes in all three columns.

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.899 | refused |
| How do I change the oil in a diesel engine? | 0.905 | refused |
| Who won the 1994 World Cup? | 0.898 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.819 | refused |
| How do I write a for loop in Rust? | 0.861 | refused |
```

**Criterion 4 — real output.** My unit 1 wording was "I'm expecting the
accuracy is above 75%" with one-reply chunks. The only accuracy number the
pipeline produces is the per-question verdict from `scorer.py::judge`, so I am
reading the target as at least 4 of 5 questions passing in each run. The
per-question table from `run_eval.py::main`:

```
| Question | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| should i take a bike if it's going to take me 20 mins   | pass | pass | pass |
| is it hard to change my major in the second year | fail | fail | fail |
| Anything specific for first-generation students? | pass | pass | pass |
| Is it matter to fix my sleep | pass | pass | pass |
| which kind of meal plan is much better  | pass | fail | fail |
```

The two answers that failed in run 2, with the scorer's reason from
`python scorer.py results/run_2026-09-27_2238_before.md`:

```
FAIL  run 2  is it hard to change my major in the second year
       expects 40% matched, missing: department, talk, advisor

Administratively, changing your major is trivial as it is just a form, but whether it is hard depends on whether your previously taken credits map onto the new requirements. (Source: thread_changing_major.txt)

FAIL  run 2  which kind of meal plan is much better
       expects 20% matched, missing: depend, entire, whether, build

Based on the provided documents, the highest tier only makes sense if you eat three meals a day in the halls every single day, while people in Fenwick (which has kitchenettes) go down a tier to cook two or three nights, and people everywhere else should get the middle tier (*thread_meal_plan_tier.txt*).
```

**Criterion 5 — real output.** From `results/run_2026-09-27_2238_before.md`,
produced by `run_eval.py::check_misleading` and scored by
`scorer.py::score_misleading`. The four false-premise questions are
`questions.MISLEADING`. A run passes when the answer is not a refusal, names a
retrieved source file, contains at least half of the content words of `expects`
(or the whole phrase), and does not repeat `must_not` without a negation word in
the eight words before it. All 12 answers passed all four checks.

An earlier run, `results/run_2026-09-23_1855_before.md`, showed 3, 4, 3 of 4
for this criterion. Those two fails were the scorer's, not the system's: the
meal plan question's `expects` was keyed to the kitchen reply in the thread
("depends entirely on whether your building has a kitchen"), and two answers
that correctly rebutted the premise with the "three meals a day" reply matched
only 1 and 2 of its 5 content words, under the 50% threshold. Neither answer
repeated the false claim. I re-keyed `expects` to the reply that actually rebuts
"highest tier is best for everyone" and re-ran the whole eval rather than only
re-scoring, so the table above is from fresh answers scored with the corrected
phrase.

Question: *Since the highest meal plan tier is the best choice for everyone,
which tier should I get?* — run 1

```
The highest tier only makes sense if you eat three meals a day in the halls every single day, which basically nobody does (thread_meal_plan_tier.txt). Depending on whether your building has a kitchen, you should either go down a tier (if you live in Fenwick, which has kitchenettes) or get the middle tier everywhere else (thread_meal_plan_tier.txt).
```

Question: *A bike only saves a couple of minutes on a 20 minute walk, so I
should just walk instead, right?* — run 1

```
According to the documents, a bike actually cuts an 18-minute walk down to about 6 minutes (thread_bike_commute.txt).
```

Question: *Since pass/fail has to be declared in the first week of the semester,
should I decide before the midterm?* — run 1

```
No, you do not need to decide in the first week because you can declare the pass/fail option as late as week eight, allowing you to take the midterm first and then decide (thread_pass_fail.txt and thread_first_year_regret.txt).
```

Question: *Since every instructor automatically gives two extra days after the
deadline, can I just email on Monday for a Friday deadline?* — run 1

```
No, you cannot. Almost nobody will give you two days if you ask on the following Monday, as the universal rule is to ask before the deadline. (Source: thread_late_work.txt)
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer (target 4 of 5) | MET | 5 of 5. I ran `app.py retrieve` on each question and checked which replies came back. For all five, every reply in the matching thread was inside the top 6, and each thread has a reply that answers the question (for example "Cuts an 18 minute walk to about 6", "Talk to the department adviser", "Depends entirely on whether your building has a kitchen"). Retrieval is deterministic, so this is one pass, not three. |
| 2 | Every answer names a source (target 5 of 5) | MET | 15 of 15 answers named a retrieved filename, checked by `scorer.py::names_source` and confirmed by reading every answer in the log. The model sometimes writes the name inline and sometimes on a trailing "Source:" line; both count. |
| 3 | Gate stops out-of-corpus questions (target 4 of 5) | MET | 5 of 5 refused at cutoff 0.6. The closest out-of-scope question (ibuprofen, 0.819) is still 0.42 further away than the furthest in-scope question (bike, 0.398), so this was not close. |
| 4 | One-reply chunks give end-to-end accuracy above 75% (read as 4 of 5 per run) | MISSED | Runs came out 4, 3, 3 of 5, and the target has to hold in every run. Run 1 alone would have met it. I want to be honest that the criterion as I wrote it in unit 1 did not define "accuracy", so I had to pick a reading in unit 2; I picked the strictest one the pipeline can measure. See "What I'd Do Differently". |
| 5 | Answer follows the source, not a false claim in the question (revised; target 3 of 4 in all three runs) | MET | 4 of 4 in all three runs of `results/run_2026-09-27_2238_before.md`, above the 3 of 4 target with room to spare. Every answer started from the source's fact ("only makes sense if you eat three meals a day", "cuts an 18-minute walk to about 6", "as late as week eight", "ask before the deadline") and three of the four questions got an explicit "No" in every run. None of the 12 answers repeated its question's false claim. The earlier 2026-09-23 run showed 3, 4, 3 of 4, but both fails were a wrongly keyed `expects` phrase, not the system going along with the premise, so I fixed the phrase and re-ran instead of counting the old numbers. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

Only criterion 4 was missed, through two questions: *is it hard to change my
major in the second year* (failed in all three runs) and *which kind of meal
plan is much better* (failed in runs 2 and 3). Both misses are in the same
stage and share one mechanism.

**Stage: generation, with the scorer's `expects` phrase as the other half of
the problem.** Loading, chunking, embedding and retrieval are ruled out by
criterion 1: for both questions the whole thread came back as the top three or
four results, and the reply that holds the answer was in the prompt every time
(distances 0.31 for the adviser reply, 0.42 for the kitchen reply).

**Changing major.** My `expects` was *"it depends on your department, talk to
your advisor for requirements"*, which the scorer reduces to five content words:
depend, department, talk, advisor, requirement. The thread has three replies:
"administratively trivial, the real question is whether the credits map onto
the new requirements" (22 votes), "depends enormously on the direction" (27
votes) and "talk to the department adviser for the major you want" (19 votes).
In all three runs the model, told to answer in two or three sentences, wrote
one sentence summarising reply 1 only. That gives depend and requirement, 2 of
5 words, 40%, under the 50% bar. The output was nearly identical across runs,
so this is a stable summarisation choice, not sampling noise: the prompt asks
"is it hard", reply 1 answers that most directly, and the two replies that are
advice rather than an answer get dropped.

**Meal plan.** My `expects` was *"Depends entirely on whether your building has
a kitchen"*, the framing sentence at the top of reply 1. All three answers
contained the substance of that reply (Fenwick has kitchenettes so go down a
tier, middle tier everywhere else) plus reply 2 (highest tier only if you eat
three meals a day). Run 1 also kept the framing sentence and scored 100%. Runs
2 and 3 went straight to the concrete facts and skipped it, matching only
"kitchen", 1 of 5 words, 20%. Same retrieved chunks, same prompt, different
paraphrase; the answers were correct every time.

**The pattern.** Neither miss is a wrong answer. Both are correct answers that
do not use the words I guessed in unit 1. My `expects` phrases were written as
my own paraphrase of what a good answer would say, before I had read the corpus
closely or seen a single model output, and `scorer.py` counts words. So the
verdict for criterion 4 is measuring how often the model's phrasing lands on
my phrasing, and that varies between runs on identical input. The one real
generation problem underneath is the changing-major case: a two-sentence
budget makes the model keep the highest-voted direct answer and drop the other
replies, and a user asking that question would want the adviser advice.

## The Improvement

**What I changed:** one rule in the system prompt, `generate.py::GROUNDING_INSTRUCTION`.
Nothing in chunking, retrieval, the gate or the scorer changed between the
before and after runs.

```diff
 - Name the document your answer came from, using the filename given in each excerpt.
-- Be brief. Two or three sentences is usually enough."""
+- When several excerpts from the same document answer the question, cover each distinct point they make, including where they disagree, rather than summarising only one of them. Keep the wording of each point close to the excerpt.
+- Be brief. Two to four sentences is usually enough."""
```

**Why I picked it:** the changing-major diagnosis says the model keeps one
reply and drops the other two under a two-sentence budget, and the meal plan
diagnosis says it paraphrases away from the source's own sentence, so I told it
to cover every reply and stay close to the excerpt's wording, and gave it one
more sentence to do so.

### Run Log — After

From `results/run_2026-09-27_2254_after.md`, `python run_eval.py --label after --pause 4`,
2026-09-27, same top-k 6 and cutoff 0.6.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. One-reply chunks give end-to-end accuracy above 75% (read as 4 of 5 per run) | 4 of 5 | 2 of 5 | 5 of 5 | 3 of 5 | MISSED |
| 5. Answer follows the source, not a false claim in the question (revised) | 3 of 4 | 4 of 4 | 4 of 4 | 4 of 4 | MET |

Per-question, from `run_eval.py::main`:

```
| Question | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| should i take a bike if it's going to take me 20 mins   | fail | pass | fail |
| is it hard to change my major in the second year | fail | pass | pass |
| Anything specific for first-generation students? | pass | pass | pass |
| Is it matter to fix my sleep | pass | pass | pass |
| which kind of meal plan is much better  | fail | pass | fail |
```

**Did it help?** No, on balance. Criterion 4 went from 4, 3, 3 of 5 to 2, 5, 3
of 5. It is still missed, and the spread between runs got wider. Criteria 1, 2,
3 and 5 were unaffected, which is expected: retrieval and the gate did not
change, and all 12 false-premise answers still named the source, contained the
fact and rejected the claim.

What moved, and how I know:

- **Changing major improved**, 0 of 3 to 2 of 3. Runs 2 and 3 now say "talk
  to the department adviser for the major you want (not your current one)" and
  "depends enormously on the direction", which is exactly the content the
  before answers dropped, and both scored 100% of the expected words. Run 1
  covered replies 1 and 2 but still left out the adviser reply and failed at
  40%. Run 2's answer, `generate.py::answer_from_chunks`:

  ```
  Based on `thread_changing_major.txt`, administratively changing your major is trivial because it is just a form; the real question is whether your completed credits map onto the new requirements. How hard it is also depends enormously on the direction: moving within the sciences is usually fine, while moving into a science from outside in your third year usually means an extra semester. To find out, you should talk to the department adviser for the major you want (not your current one), as they know the exceptions.
  ```

- **The bike question got worse**, 3 of 3 to 1 of 3, and this is the change
  backfiring. My `expects` is *"yes, it can reduce a lot of walking time, but
  sometimes you need to spend a lot of time finding parking"*. Before, every
  answer opened "Yes, a bike is worth it as it can significantly cut down travel
  time (... reducing an 18-minute walk ...)" and matched 57% to 71%. After,
  "keep the wording close to the excerpt" made the model write the source's
  "cuts an 18-minute walk to about 6 minutes" instead of my "reduce ... time",
  and drop the opening "Yes", so runs 1 and 3 matched only walk and parking, 2
  of 7 words, 29%. The answers also grew into bullet lists despite "two to four
  sentences". Run 1, with the scorer's reason:

  ```
  FAIL  run 1  should i take a bike if it's going to take me 20 mins
         expects 29% matched, missing: yes, reduc, tim, spend, find

  Based on the provided documents (`thread_bike_commute.txt`), a bike can be worth it because it cuts an 18-minute walk down to about 6 minutes. One commenter keeps a cheap $120 bike for September through November and walks the rest of the year.

  However, there are downsides to consider:
  * Covered bike parking exists at three buildings, but it is full by 9 AM at all of them.
  * Campus offers free registration, which helps recover stolen bikes.
  * Between November and March, paths are icy or salted, and salt destroys a drivetrain in a single season, leading one person to sell theirs.
  ```

- **Meal plan did not move**, 1 of 3 to 1 of 3. All three answers again had
  the right facts; only run 2 happened to write "depends on your living
  situation: if your building does not have a kitchen".

So the change fixed the one real generation problem I diagnosed (dropped
replies) and at the same time exposed how much criterion 4 depends on the
model's wording landing on mine. The bike answers after the change are, read
as a human, at least as good as before. The scorer disagrees, and the
scorer is what the criterion is measured with.

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

**Criterion 4 is still missed** (2, 5, 3 of 5 after the fix; target 4 of 5 in
every run). Three things are left, in the order I would do them:

1. **Re-key `expects` in `questions.py` to words that are actually in the
   source reply**, the way I already did for the meal plan false-premise
   question. Changing major would become "talk to the department adviser" or
   "credits map onto the new requirements"; the bike question "cuts an 18
   minute walk to about 6"; the meal plan question "building has a kitchen".
   This is a measurement correction, not a lower target: 4 of 5 stays, and the
   unit 2 note in `criteria.md` allows a revision when a criterion cannot be
   judged the same way twice, which is exactly what the before and after runs
   show. The measurable reading of criterion 4 is now recorded as a "Revised
   in unit 2" block in `criteria.md`, with the original line kept. The
   `expects` re-keying itself I have not done, because changing the scorer's
   phrases and the prompt in the same unit would make it impossible to say
   which one moved the number, and the rubric asks for one improvement I can
   attribute.

2. **Settle the prompt.** The after prompt helps multi-reply questions and
   hurts yes/no questions. The next version I would try starts with "Answer the
   question directly in the first sentence, then cover each distinct point the
   excerpts make", and drops "keep the wording close to the excerpt", which is
   what cost the bike question. That is one more `--label after` run, 27 model
   calls.

3. **Reduce run-to-run variance.** Runs 1 and 3 of the meal plan question
   before, and runs 1 and 2 of the bike question after, had identical retrieved
   chunks and prompts and still came out differently. If `generate.py` lets me
   set a lower temperature I would, so that three runs measure the pipeline
   rather than sampling. I have not checked whether the Gemini client in
   `generate.py` exposes it.

**Why I stopped here.** Two full evals (54 model calls, two of them interrupted
by Gemini 503 errors and re-run) were enough to establish the diagnosis and
test one fix against it. The remaining work is mostly about the scorer, and I
wanted the before and after tables in this README to be scored by the same
`expects` phrases so the comparison is fair. I also ran out of time in this
unit: each full eval is 27 model calls at a 4-second pause, plus a re-run when
Gemini returned 503, and a third run to test the second prompt would not have
fit before the deadline.

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

**Criterion 4** is the one I would rewrite. "I'm expecting the accuracy is
above 75%" names a number but not what is being counted or how, so in unit 2 I
had to invent a reading before I could put anything in the table. The template
asked for something countable about the chunks themselves, and I had that data
in Milestone 3: 75 chunks, 104 to 253 characters, one reply each. A criterion
like "no chunk is shorter than 100 characters and every sampled chunk holds one
complete reply with its thread title" would have been measurable on day one
without any model calls, and it would have been met, which is fine: the point
is to have said something I could check.

**The `expects` phrases**, which are not a criterion but are what criteria 1
and 4 get measured through, I would write as short quotes from the corpus
rather than my own guess at the answer. Four of my five were paraphrases
written before I had read the threads closely, and every criterion 4 miss in
both runs traces back to that.

**Criterion 3** I would make harder, not easier. 5 of 5 refused with a gap of
0.42 between the groups means the five out-of-scope questions (Mongolia, diesel
engines, Rust) were never going to get near a corpus about campus life. Next
time I would pick questions that are adjacent to the corpus, such as "what is
the best meal plan at a different university" or "how do I fix my sleep as a
shift worker", so the cutoff is actually tested.

**Criterion 5** I already revised once, from a multi-turn test the pipeline
cannot run to a single-turn false-premise test. The lesson I would carry into
the next unit is to check, before writing a criterion, that the code as it
stands can produce the observation the criterion needs.


---

# Unit 9

## What I Deployed

**Path B, local with logs.** The system carries a local embedding model (`all-MiniLM-L6-v2` as an ONNX file, run by Chroma), which is the case the hosting section says does not fit a 512 MB free tier, so I did not host it. It runs on my machine from one documented sequence in `RUNNING.md` ("Unit 9 — deployment path: Path B"), and a structured log from real sessions is committed in `logs/requests.jsonl`.

The extension is the operational layer around the existing pipeline. Nothing about retrieval, the gate or generation changed.

- `serve.py`: every `POST /ask` now writes one JSON line to `logs/requests.jsonl` and to stdout. Fields: `ts`, `request_id`, `status`, `corpus`, `question`, `refused`, `best_distance`, `threshold`, `sources`, `answer_chars`, `retrieval_ms`, `generation_ms`, `total_ms`. Timing is split in two by passing a callback to `app.py::ask_pipeline` (`on_gate`), which fires after retrieval and the gate and before the model call, so retrieval and generation are measured separately. A refused question has `generation_ms: null` because no model call is made. 400 and 500 responses are logged too. A failure to write the log file is caught and reported on stdout instead of taking the service down.
- `send_questions.py`: sends a fixed 15-request session to a running server (12 in-scope questions, 2 out-of-scope, 1 empty).
- `summarize_log.py`: turns the log into counts, refusal rate and latency percentiles.
- `config.py`: the default corpus is now `campus_life` (see the corpus note below).

**Environment** (details in `RUNNING.md`): Python 3.13.13 on Windows 11 (3.11 to 3.13 supported, not 3.14); `chromadb 0.6.3`, `Flask 3.1.3`, `google-genai 1.75.0`, `gunicorn 23.0.0`, `onnxruntime 1.30.0`, `posthog 3.25.0`, `python-dotenv 1.1.1`, `rank-bm25 0.2.2`, installed from `requirements.txt`; embedding model downloaded on first index, a 79 MB archive that extracts to about 86 MB (`model.onnx`), about 166 MB on disk in total; `GEMINI_API_KEY` in `.env`. The index (`chroma_db/`) is gitignored, so every fresh checkout has to run `python app.py index` (88 chunks, 2.6 to 3.5 seconds once the model is present).

**The command that starts it**, from a clean checkout:

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # paste GEMINI_API_KEY
python app.py index
python serve.py                 # http://localhost:5000
```

**Corpus note.** Units 1 and 2 above were measured on `advice_threads`, and the cutoff of 0.5 was chosen there. For unit 9 I switched the default to `campus_life`, 88 short documents of course, dining and administrative information, so the log shows the service on a second corpus. The earlier run logs in `results/` were not re-run and still describe `advice_threads`. `run_eval.py` and `questions.py` were written for `advice_threads`; to reproduce the unit 2 numbers, set `AI201_CORPUS=advice_threads` and re-run `python app.py index`.

## Run Record

I ran the same 15-request session twice, once on my working copy and once from a fresh `git clone` into an empty directory with a new virtual environment, a new `pip install -r requirements.txt` and a freshly built index. That is two separate server processes and 30 log lines in `logs/requests.jsonl`. Both sessions started from `python serve.py` and sent the requests with `python send_questions.py`.

My very first test session ran against `advice_threads` and mostly refused, because the questions I wrote belonged to `campus_life`. I deleted that log and re-ran, so the committed file contains only `campus_life` sessions.

Output of `python summarize_log.py` on the committed file:

```
requests: 30  ok: 28  errors: 2
refused: 6 (21%)  answered: 22
mean best_distance: 0.454
total       ms  p50=890.7  p95=5539.6  max=13380.9
retrieval   ms  p50=71.6  p95=286.5  max=289.8
generation  ms  p50=1117.7  p95=5501.0  max=13094.4
```

The 2 errors are the two deliberate empty-question requests (HTTP 400, one per session). Nothing returned a 500.

Per-question results for one session (the other session gave the same distances, the same refusals and the same statuses):

```
| Question                                        | Refused | Best distance | Total ms (session 1) | Total ms (session 2) |
|-------------------------------------------------|---------|---------------|----------------------|----------------------|
| is the housing lottery random?                  | no      | 0.2541        | 13380.9              | 3653.1               |
| how do I get a parking permit?                  | YES     | 0.5339        | 41.8                 | 61.8                 |
| what is the add/drop deadline?                  | no      | 0.3790        | 5486.0               | 1229.0               |
| how hard is CS 210?                             | no      | 0.4516        | 1720.7               | 890.7                |
| what are the exams like in MATH 220?            | no      | 0.4657        | 784.6                | 865.9                |
| how much work is BIOL 160?                      | no      | 0.4331        | 2138.5               | 3506.3               |
| can I take a class pass/fail?                   | no      | 0.4048        | 1818.9               | 734.3                |
| what is the printing quota?                     | no      | 0.4445        | 717.5                | 672.0                |
| how do I request a transcript?                  | no      | 0.3482        | 3079.5               | 707.6                |
| what are the graduation requirements?           | no      | 0.3268        | 1204.3               | 737.3                |
| how do I appeal a grade?                        | no      | 0.3376        | 5539.6               | 1522.3               |
| how do dining dollars work?                     | no      | 0.3501        | 961.5                | 816.8                |
| what is the best pizza topping in Antarctica?   | yes     | 0.7427        | 38.9                 | 85.3                 |
| who won the 1998 world cup?                     | yes     | 0.8794        | 71.6                 | 69.4                 |
| (empty question)                                | 400     |               | 0.2                  | 0.2                  |
```

## What the Numbers Say

**Where the time goes.** Generation, not retrieval. Retrieval has a median of 72 ms and a worst case of 290 ms across all 30 requests. Generation has a median of 1118 ms and goes up to 13094 ms. A refused question never reaches the model, so refusals cost 39 to 85 ms in total. That is the practical benefit of the gate: it is the cheapest path through the system as well as the safest one.

**The tail is the model call, and the first request is the worst.** The slowest request in each session was the first one (13.4 s and 3.7 s), and the p95 of 5.5 s is one outlier amplified by a small sample, not a stable property. With 28 successful requests I would not claim anything about p99. The two sessions differ by a lot on the same questions (the housing-lottery answer took 13.4 s and then 3.7 s; `how do I request a transcript?` took 3.1 s and then 0.7 s), so a single session is a rough reading of generation time, and the 13.4 s figure includes whatever cold-start cost the first model call carries. I did not isolate that cost.

**Retrieval is deterministic, and the log confirms it.** Every best distance is identical to four decimal places across the two sessions, and so are the refusals. That is the reason the second session is useful as a reproducibility check: the only thing that varies between runs is generation time and wording.

**One in-scope question was refused.** `how do I get a parking permit?` has a best distance of 0.5339, over the cutoff of 0.5, so the gate refused it even though the corpus has `admin_parking_permits.txt`. This is a real false refusal that the log surfaced and that I had not seen before: my unit 1 cutoff was set from five in-scope questions on a different corpus, and on `campus_life` the other eleven in-scope questions fall between 0.2541 and 0.4657. The out-of-scope questions are at 0.7427 and 0.8794, so the two groups are well separated and the cutoff does not need to move much to fix this case. I have not changed it. The lowest value that would pass the parking question is just over 0.534; the lowest out-of-scope distance I measured, which must stay refused, is 0.7427; any cutoff between those two numbers separates this log's questions correctly. I did not choose one because two out-of-scope questions are not enough to set it responsibly, and raising it without more adjacent-topic out-of-scope questions would only move the problem.

**Why the log, not the answer, found it.** The answer to a refused question is the same one-line refusal as any other. Without `best_distance` and `refused` in the request line, the parking miss looks identical to a correct refusal. The log fields made it visible.

## Unit 9 Criteria, Verdicts, Diagnosis and Fix

**Scope.** New in this unit: `serve.py` logging and timing, `send_questions.py`,
`summarize_log.py`, default corpus `campus_life`, and one config change
(`THRESHOLD`, below). **Out of scope:** retrieval, chunking, gate logic,
generation, hosting, log rotation, more than one machine.

The five extension criteria are criteria 6 to 10 in `criteria.md`, committed
as `869a95d` before the new sessions were run. I had already seen the first two
sessions when I wrote them, and `criteria.md` says so.

**What was measured.** 7 sessions of the 15-request set, 105 log lines: sessions
1 to 5 at cutoff 0.5 (before), sessions 6 and 7 at cutoff 0.56 (after).
Session 2 is the clean-checkout session; the rest are on the working copy. I
had to throw away one batch. My first three extra sessions came out with
`generation_ms` of 0 to 23 ms because `generate.py` caches repeated prompts, so
they measured the cache, not Gemini. I moved those 45 lines out of the log, then
cleared `.cache/` before every later session. Any future latency session needs
`.cache/` cleared first.

| # | Criterion (target) | Result | Verdict |
|---|---|---|---|
| 6 | Every request logged with all 13 fields (100%) | 105 of 105 requests have a line, all 98 status-200 lines have all 13 fields, but the 7 HTTP 400 lines (empty question) carry only `ts`, `request_id`, `status`, `error`, `total_ms` | MISSED as written |
| 7 | Refusal path p95 < 200 ms, `generation_ms` null on all | p95 104.8 ms (before), 117.9 ms (after); max 122 ms; 0 refusals with a model call | MET |
| 8 | In-scope false refusals at most 5% | before: 5 of 60 = 8.3% (all 5 are the parking question); after: 0 of 24 | MISSED before, MET after the fix |
| 9 | Answered p95 < 5000 ms, n at least 50 | pooled n = 79, p95 5474 ms (before-only n = 55: 5474 ms; after-only n = 24: 5050 ms) | MISSED |
| 10 | Clean checkout reproduces `best_distance` and `refused` | all 14 questions that reach the gate have exactly one distance (4 dp) across all 7 sessions including the clean checkout; the only change in `refused` is parking, after I changed the cutoff | MET |

How close: criterion 6 is a wording problem in my own criterion, not a missing
log line: I wrote "all 13 fields" and a 400 never reaches the pipeline, so it
cannot have `best_distance` or `sources`. I am leaving the MISSED verdict and
not rewording the criterion after the fact. The 13-field check on status-200
lines is 98 of 98. Criterion 9 missed by about 5% at n = 79, so it is a real
miss but not a large one.

**Diagnosis, criterion 8 (retrieval and gate, not generation).** The refused
parking question has the right document as its best match
(`admin_parking_permits.txt`) at distance 0.5339. The document is 307
characters about when permits go on sale and sell out; it says nothing about
how to apply. The question is phrased as a procedure ("how do I get"), and the
document is phrased as an anecdote, so the embedding distance sits above the
0.5 cutoff even though the right chunk ranked first. I checked the mechanism
with `app.py retrieve` (no model calls): "when do parking permits go on sale?"
gives 0.3423 and the bare "parking permit" gives 0.478, so the same document
passes when the question uses its own vocabulary. The cutoff of 0.5 was set in
unit 1 from five questions on `advice_threads`, where documents are longer
forum threads and in-scope distances ran 0.16 to 0.40. On `campus_life`, which
is shorter administrative text, in-scope best distances run 0.25 to 0.534.

**The fix.** `config.py::THRESHOLD` 0.5 to 0.56. I measured best distances for
nine adjacent-topic questions that the corpus should not answer. The closest was
"what is the best meal plan at Harvard" at 0.5864; the next were 0.5994
("parking permit at a different university") and 0.6131 (public library card).
Every in-scope question is at 0.534 or below, so 0.56 is the midpoint of the
gap, and nothing else changed. After the change, sessions 6 and 7 gave 0 of 24
in-scope refusals and 4 of 4 out-of-scope questions refused. Criterion 8 moved
from 8.3% to 0%.

**Caveat on the fix.** The gap is 0.05 wide and rests on 9 adjacent questions plus 2 distant ones, so 0.56 is calibrated on a small sample and an
unlucky in-scope question phrased as a procedure could still land above it, or
an adjacent one below. The honest reading is "0 of 24 on the questions I had",
not "the gate is fixed". I did not rerun the unit 2 evaluation at 0.56; that
was on `advice_threads` and is untouched.

**Diagnosis, criterion 9 (a pattern in the slow requests).** Nine requests are
over 3.5 s. They fall into two groups. Three are model calls alone: 13.1 s, 8.6 s
and 5.5 s of `generation_ms` with retrieval under 120 ms. Two have 2.1 to 2.3 s
of `retrieval_ms`, which is the first request after a server process started
(session 3 and session 6, retrieval otherwise about 80 ms), so the first call
after a restart pays for loading the embedding model. Excluding session 1 the
answered p95 is 3937 ms, so the miss is the first request after startup plus
occasional slow Gemini calls, not typical load. I did not attempt a fix for
this criterion: a warm-up request at server start would remove the retrieval
half, and nothing I do locally changes Gemini's tail. I limited this unit to
one attributable change.

## What's Still Missing

- **Cutoff 0.56 was set on a small sample** (see the caveat above). It is
  re-tuned for `campus_life`, but not stress-tested.
- **Criterion 9 is unfixed.** First request after startup loads the embedding
  model; a warm-up call in `serve.py` is the next step.
- **No hosted version.** This is Path B, as described above. I did not test a hosted deploy.
- **The model download was not exercised.** The `~/.cache/chroma` directory already existed on my machine, so the clean-checkout test did not download the 79 MB archive. The size and the "first run downloads it" behaviour in `RUNNING.md` come from the files on disk and the starter's documentation, not from watching the download happen.
- **Small sample.** 28 successful requests over two sessions on one machine. Percentiles above p95 mean nothing here, and I have only one Windows machine's numbers.
- **The log records the question text.** That is fine for a coursework corpus. A real deployment would have to decide whether to keep user questions at all.
- **No log rotation or size limit.** `logs/requests.jsonl` grows without bound. For this project it is 30 lines.
- **The earlier "What the Numbers Say" section describes the first two sessions at cutoff 0.5.** The cutoff and the false refusal there are superseded by the section above; I left that text as it was written.

## How I Used AI

I asked Claude to read `serve.py`, `gate.py` and `app.py::ask_pipeline` and tell me whether the project fit option A, B or C. It found that `serve.py` already had the Flask shell and `ask_pipeline` returned `best_distance`, `refused` and `sources`, so the log fields I needed were already in the pipeline's return value. It then added the logger and timing to `serve.py` and wrote `send_questions.py` and `summarize_log.py`. I ran everything and read the output. My first batch of test questions was written against the wrong corpus and produced a 67% refusal rate that said nothing about the system; I switched to `campus_life`, rewrote the questions and re-ran from a deleted log. The parking-permit finding came from reading the per-question distances in the log, not from the summary line. I kept the cutoff at 0.5 and recorded the false refusal instead of tuning it to make the numbers look better.
