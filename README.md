# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

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

<!-- 补充：哪些是你自己改过或不同意的。比如：criterion 4 的解读（"至少 4/5 通过"）是 Claude 提的，你是否接受；提示词改动你是否保留。 -->


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
by `python run_eval.py --label before --pause 4` on 2026-09-27 with top-k 6 and
relevance cutoff 0.6 (the value in `config.py`).

<!-- NOTE TO SELF: unit 1 above says "My relevance cutoff: 0.5", but
     config.py still has THRESHOLD = 0.6 and both run logs used 0.6. Either
     change config.py to 0.5 and re-run, or correct the unit 1 line. -->

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
   show. I would record it as a "Revised in unit 2" block under criterion 4 and
   keep the original line visible. I have not done this yet because changing
   the scorer's phrases and the prompt in the same unit would make it
   impossible to say which one moved the number, and the rubric asks for one
   improvement I can attribute.

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
`expects` phrases so the comparison is fair.

<!-- 这里补一句你自己的原因，比如时间、或者你觉得哪一步不值得再花模型调用。 -->

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

<!-- 如果你想只保留一条，留 criterion 4 那段。 -->
