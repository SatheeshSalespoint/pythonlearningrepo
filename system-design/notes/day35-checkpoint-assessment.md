# Day 35: Checkpoint Assessment (Days 22–34 Review)

**Date:** 2026-09-08
**Duration:** ~75 mins
**Status:** ✅ Complete
**Format:** Interview-style assessment, cold recall, no notes
**Overall Score:** 6.0/10
**Verdict:** ⚠️ **Not yet ready for Phase 3 (Hard systems).** Bridge phase required.

---

## Purpose

Planned decision point at end of Phase 2. Assess against the six criteria set on
Day 21 and decide whether to proceed to Days 36–45 (Hard) or adjust the plan.

Assessment was deliberately **cold** — no notes, no lookups. The question was not
"can you recognise the right answer" but "can you retrieve it under pressure."

---

## Round Scores

| Round | Criterion | Score | Result |
|---|---|---|---|
| 1 | Estimate scale correctly | 7.5/10 | ✅ Pass |
| 2 | Identify bottlenecks immediately | 6.5/10 | ⚠️ Partial |
| 3 | Consistency/availability tradeoffs | 5.0/10 | ❌ Fail |
| 4 | Ask good architectural questions | 7.0/10 | ⚠️ Partial |
| 5 | Handle multiple constraints at once | 4.0/10 | ❌ Fail |
| 6 | Real-time + strong consistency | — | Not assessed (fatigue) |

---

## Round 1 — Scale Estimation (7.5/10) ✅

**Scenario:** 8,000 merchants, 220 txn/day each, 80% in a 9-hour window.

**Landed:**
- All storage arithmetic correct, first attempt:
  `400 B × 1.76M = 704 MB/day → 257 GB/yr`
  `1.2 KB × 1.76M = 2.11 GB/day → 766 GB/yr → 5.37 TB over 7 years`
- Peak write QPS correct: `1,408,000 / 32,400 = 43/sec`
- Read side correct: `8,000 × 14 × 6 = 672,000/day → 16.6/sec peak`
- **Correctly identified the system as WRITE-heavy** (1 : 2.6) — the Day 34
  inversion transferred. Most people see "dashboard" and say read-heavy.

**Missed:**
- **Labelled the trough as the average.** Computed 6.5/sec (the off-peak rate:
  `352,000 / 54,000`) and called it the average. True average is
  `1,760,000 / 86,400 = 20.4/sec`.
  Consequence: "6 → 43" implies a 7× spike; the truth is 20 → 43, a 2.1×
  multiplier. Two different architectures get argued from those two framings.
- Did not mention that raw payload ≠ provisioned disk. Indexes + row overhead +
  replication ≈ 2.5–3×. The 5.37 TB audit store is a ~15 TB procurement item.

**The concept not retrievable cold — precompute threshold:**

```
Aggregate read:write tells you what the SYSTEM is.
Per-key reads-per-write tells you what to BUILD.
Precompute only when that number is comfortably above 1.
```

Per merchant per day: 84 reads vs 220 writes = **0.38 reads per write.**
Every precomputed total is overwritten ~2.6× before anyone reads it. Caching and
write-time precomputation are both *negative value* here. Day 34's leaderboard
came out the opposite way because a leaderboard is viewed far more often than it
changes. **Same structure, opposite verdict, and the deciding number is per-key
reads-per-write.** Correct answer here: compute on read, or batch-aggregate
(the Day 22 answer).

---

## Round 2 — Bottleneck Identification (6.5/10) ⚠️

**Scenario:** End-of-day reconciliation. 11pm start, 7am deadline, external
settlement file lands 10:45pm.

**Landed:**
- Correct arithmetic: `1.76M / 28,800s = 61/sec`, ×2 reads = 122 read QPS
- Correct conclusion: **"Read not an issue."**

**Missed — and this is a communication failure, not a knowledge failure:**

Having reached the right answer, abandoned it under a leading question and
manufactured a bottleneck (email). 8,000 emails over 10 minutes is 13/sec —
a rounding error for any provider.

Every stage had 15–100× headroom:

| Stage | Load | Headroom |
|---|---|---|
| Read transactions | 704 MB over 8 hrs | ~100× |
| Compare | 61/sec | ~100× |
| Generate 8,000 Excel files | ~27 min single-threaded | ~17× |
| Send 8,000 emails | 13/sec for 10 min | ~50× |

**"There is no throughput bottleneck here" was the complete, correct answer.**

**What actually breaks first — the schedule, not capacity:**
- The 10:45pm file drop is the acquirer's promise, not a guarantee. A 2am
  delivery turns an 8-hour window into 5.
- The job runs **once**. Dies at 1am → no retry, nobody awake.
- The 7am deadline is hard.

> For a batch job with large throughput headroom, the bottleneck is **the
> critical path and its recovery story**, never QPS.

**What breaks second — the cutoff boundary.** Your day ends at midnight NZ; the
acquirer's settlement day ends on their clock, their timezone, their cutoff.
Boundary transactions land on different days on each side and surface as
mismatches that aren't mismatches. 0.1% of 1.76M = **1,760 false flags nightly**
— a *correctness* bottleneck, which on a reconciliation system is the one that
actually kills you.

---

## Round 3 — Consistency Tradeoffs (5.0/10) ❌ WEAKEST ROUND

**Scenario:** Merchant hits Refund → writes to leader → dashboard reads a
follower with 400ms lag.

**Landed:** Described the stale-read problem accurately and challenged the
premise unprompted (good Day 34 instinct).

**Missed — the term:** this is **read-your-own-writes consistency**. Described
precisely, could not name it. The label buys credibility in three words.

**Core failure — conflated consistency with availability.**
Two of three proposed fixes answered *"what if the leader dies"*, a question that
was never asked. Nothing in the scenario was broken: healthy leader, healthy
follower, normal 400ms lag. **Failover fixes solve nothing here.**

| Proposed fix | What it actually solves |
|---|---|
| Critical reads → leader | ✅ Replication lag |
| Two leaders, synced | ❌ Leader failure — and *worsens* consistency |
| AOF + follower promotion | ❌ Leader failure / recovery |

**"Two leaders, no eventual consistency issue" is backwards.** Two leaders both
accepting writes is **multi-leader replication** — same row writable in two
places, requiring conflict resolution (LWW, vector clocks, CRDTs). It is the
*most* eventually-consistent topology available, and close to disqualifying for
fintech refunds.

**Costs were not stated for any fix.** That half of the question *was* the
criterion — tradeoff articulation is the skill, not fix enumeration.

### The three fixes with their costs

1. **Route critical reads to the leader.**
   *Cost:* gave up read scaling for that data; leader serves writes + hot reads.
   Fine at 43 writes/sec — quietly stops working at 10×.
2. **Sticky routing / read-your-own-writes.** Pin *that merchant* to the leader
   for ~2s after their write, or track the write's log position and only serve
   from a follower caught up past it.
   *Cost:* session state, routing complexity, uneven follower load.
   Strictly better than #1 — same guarantee, keeps read scaling for everyone else.
3. **Synchronous replication.** Leader doesn't ack until a follower confirms.
   *Cost:* +1 network round trip on every write, and **availability drops** — a
   slow or dead follower now blocks writes. CAP in its purest form.

### The part that matters most (answered "no change" — it changes decisively)

A *second* merchant viewing a shared balance affected by the same refund:

- **Read-your-own-writes does not apply** — they made no write.
- **Fix #2 evaporates** — you cannot pin a user to the leader on a write they
  never made. No session, no trigger, no log position.
- **Different guarantee needed:** *monotonic reads* — may be stale, must never
  appear to move backwards.
- **The business answer flips:** 400ms stale on *your own* refund is a support
  ticket. 400ms stale on *someone else's* is invisible and fine.

> **Consistency is not a property of the data. It is a property of the
> relationship between a reader and a write.** Same row, same lag, same
> infrastructure, different observer, different correct answer.

Current mental model is "critical vs non-critical tables" — Day 19's model,
too coarse. **This is the single biggest gap found.**

---

## Round 4 — Asking Questions (7.0/10) ⚠️

**Scenario:** *"Merchants upload invoices and receipts. They need to find them
later. Can you build that?"* — Role reversal, ask don't design.

**Landed:**
- Asked about **retention** (7 years) and **failure handling** — both unusual and
  both good. Most candidates ask only about features.
- **Stopped at seven questions.** No nervous rambling.

**Missed:**
- Four of seven questions were the same question — "how big is it?" The sizing
  reflex from Days 20–34 firing on autopilot, spent on comfortable ground.
- *"How much storage will be allocated?"* is backwards — the architect tells the
  stakeholder that, and the answer was already in hand:
  `8,000 × 15 × 1.5 MB = 180 GB/day → 65 TB/yr → 460 TB over 7 years`

**The question not asked — "they need to FIND them later." Find them HOW?**
- By filename and date → a DB column and a file store. **Two weeks.**
- By content ("every invoice mentioning ACME Ltd") → **OCR on 1.5 MB phone
  photos, extraction pipeline, full-text index over 460 TB. Six months.**

Four words in a one-sentence brief, swinging the project by an order of
magnitude — the highest-uncertainty item in the room, untouched.
**Note:** that system is OCR + inverted index = **Day 33**, the open day. The
gap in the roadmap surfaced directly as a gap in the questioning.

**Three more worth asking:** who may read a document (cross-tenant leak =
regulatory event) and does AUS data have to *stay* in AUS; can a merchant delete
(7-year retention vs privacy-law deletion **directly contradict**); and how often
a document is read after upload (hot vs archival ≈ 10× cost — the same
*reads-per-write* question from Round 1 in a different costume).

---

## Round 5 — Multiple Constraints (4.0/10) ❌

**Scenario:** 460 TB / 7 yr under $3,000/mo; NZ–AUS residency; 2-second SLA for
last 90 days; tamper-evident audit queryable for 7 years.

**Result:** Worked each constraint in isolation, never crossed them — which is
precisely what the criterion tests. Part (b) not attempted.

**(a) Sharpest pair: Cost × Residency.**
The mechanism given was wrong (described an AUS merchant fetching an NZ
merchant's document — that is **cross-tenant access, which must never happen**).
Residency is not about who reads across a border; it is about **where the bytes
physically sit.**

Cheap storage comes from **consolidation** — one pool, volume pricing, one
archival tier, one lifecycle policy. Residency **forbids consolidation**: two
complete storage estates, and dual-country merchants may store documents twice.

Subtler pair — **Residency × Audit**: a tamper-evident hash chain cannot span
regions, so you keep two independent chains, and "every access by this
dual-country merchant" becomes a cross-border join you may not perform naively.

**(c) Cheapest constraint: the retrieval SLA** — right mechanism (tiering)
attached to the wrong constraint. The arithmetic that makes the case:

```
Hot data  = 180 GB/day × 90 days = 16.2 TB
Total     = 460 TB
Hot share = 16.2 / 460 = 3.5%

16.2 TB hot     × ~$0.023/GB/mo  ≈  $373/mo
444 TB archive  × ~$0.001/GB/mo  ≈  $440/mo
                                    ~$813/mo   ← well under $3,000
```

> An SLA that sounds expensive is cheap because **recency is a tiny slice of
> retention.** The 2-second guarantee only binds 3.5% of the data.

**(b) The design:**

```
Per region (NZ, AUS) — fully independent, nothing crosses:

  0–90 days   → hot object storage      2s SLA met directly
  90d–7yr     → deep archive            hours to retrieve
  Metadata    → regional DB             never archived; tiny, always hot
  Audit       → append-only, hash-chained, regional
```

The move that makes it work: **separate metadata from bytes.** Filename,
merchant, date, tags — kilobytes, always hot, always searchable. The 1.5 MB blob
tiers to archive. Search stays instant across all 7 years even when the document
itself takes an hour to retrieve.

**Relax constraint 3 for old documents, and price the relaxation out loud:**

> "Anything from the last 90 days opens instantly. Older documents are archived —
> you request it, we email you when it's ready, typically within a few hours.
> That choice is what keeps this under $1,000/month instead of $10,000. If any
> workflow needs seven-year-old documents on demand, tell me now, because that's
> the expensive requirement — not the storage."

Handing the decision back **with its cost attached** is what gets sign-off.

---

## The Pattern Across All Five Rounds

**Strong at quantifying what you are given. Weak at interrogating what you are
given.**

Rounds 2, 3, 4 and 5 each turned on something in the *framing* that needed
challenging rather than computing:

- R2 — the premise that a bottleneck existed at all
- R3 — the assumption that consistency is a property of tables, not observers
- R4 — the four ambiguous words in the brief
- R5 — the assumption that constraints can be evaluated one at a time

Arithmetic is now reliable (Day 33's weakness, closed). The next capability is
**challenging the frame**, which was demonstrated on Day 34 (pushing back on the
unsourced number) but did not generalise.

---

## Verdict Against the Six Criteria

| Criterion | Status |
|---|---|
| Can estimate scale correctly | ✅ **Pass** — reliable and fast |
| Identify bottlenecks immediately | ⚠️ **Partial** — method sound, conviction weak |
| Ask good architectural questions | ⚠️ **Partial** — good on lifecycle/failure, avoids ambiguity |
| Consistency/availability tradeoffs deeply | ❌ **Fail** — conflated with availability |
| Handle multiple constraints simultaneously | ❌ **Fail** — handled serially |
| Ready for real-time + strong consistency | ❌ **Not demonstrated** |

**Decision: do not proceed directly to Phase 3 (Days 36–45).**

Phase 3 opens with Uber — real-time matching under strong consistency. That
system is a *pure* Round 3 + Round 5 problem: overlapping consistency guarantees
under simultaneous constraints. Both are current fail states. Going in now means
learning the hard systems on top of an unstable foundation.

This is not a setback. **Two of six criteria failing at a checkpoint is exactly
what a checkpoint is for** — the alternative was discovering it on Day 43 with
five confusing days behind it.

---

## Adjusted Plan: Bridge Phase, Days 36–41

Five days closing the two failed criteria before Phase 3 reopens on Day 42.

| Day | Focus | Target |
|---|---|---|
| **36** | **Consistency models, mechanism-first** | Read-your-own-writes, monotonic reads, causal, linearizable — each with a worked example. Load the vocabulary before designing. |
| **37** | **Day 33 finish — Search Engine** | Close the open day: ranking, sharding, freshness, tenant isolation. Directly feeds the Round 4 gap. |
| **38** | **Applied session** (not planned — own take-home) | Scaled the Xe rate-alerts take-home to production. Not a substitute for the re-test below, but real practice on the same skill (guarantee/cost, dual-write). |
| **39** | **Consistency re-test** | Re-run Round 3 cold, plus two new scenarios. Must reach 8/10 to advance. |
| **40** | **Multi-constraint drill** | Three scenarios with deliberately conflicting constraints. Practise naming the conflicting *pair* and pricing the relaxation. |
| **41** | **Round 6 + re-assessment** | Real-time/strong consistency round, then re-score all six criteria. |

**Gate for Phase 3:** consistency ≥ 8/10 **and** multi-constraint ≥ 7/10 on Day 41.

**Standing drill, every day from here** — before designing anything, ask:
> *"What in this brief am I taking as given that I should be challenging?"*

That single habit addresses all four of the rounds that went sideways.

---

## Communication Notes

Measured against the 8.5/10 target from the coaching plan.

**Improved:** arithmetic is written out with zeros (Day 33 fix held); stopped
questioning at a sensible point in Round 4; said "I can't remember" plainly
rather than bluffing — genuinely good, and rare.

**To work on:**
- **Don't abandon a correct answer under pressure** (Round 2). When the numbers
  say there is no problem, say so and redirect to where the risk actually lives.
  Manufacturing an answer to satisfy the interviewer reads as low confidence.
- **State costs unprompted.** Every proposal needs "…and what this costs me is X."
  Currently proposals arrive bare.
- **Use the vocabulary.** "Read-your-own-writes", "monotonic reads",
  "multi-leader" — the concepts are understood; the terms are missing, and terms
  are how seniority is read in a 45-minute interview.

---

## Next: Day 36 — Consistency Models (mechanism-first)

Genuinely new material, so it is taught before it is tested: worked examples of
each guarantee first, bottleneck questions after.
