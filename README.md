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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

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

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
