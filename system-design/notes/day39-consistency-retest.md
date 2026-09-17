# Day 39: Consistency Re-Test

**Date:** 2026-09-17
**Duration:** ~45 mins
**Status:** ✅ Complete — gate cleared
**Phase:** 2.5 Bridge (Days 36–41)
**Format:** Cold, no notes — Round 3 re-run from Day 35, plus two new scenarios
**Overall Score:** 8.2/10
**Gate:** Consistency ≥ 8/10 for Phase 3 — **PASSED**

---

## Round 1 — Re-run: Merchant Refund / Follower Lag (8.5/10)

Same scenario as Day 35 Round 3 (5.0/10 fail), cold.

**Landed, unprompted this time:**
- Named "read-your-own-writes" correctly, first try
- Led with the cheap fix (sticky routing) instead of jumping to failover/multi-leader
- Stated a cost for every proposal without being asked
- On the follow-up (second merchant, no write of their own), independently
  reconstructed the monotonic-reads case: recognized that reading from two
  different followers with different lag could show the balance moving
  *backward*, and proposed pinning to the same follower to prevent it —
  before being told the term existed.
- When asked why permanent leader-reads become unaffordable, answered in pure
  capacity terms ("leader gets more load than it can take, causes latency/
  unavailability") — **did not** reach for "if the leader dies," the exact
  tell flagged on Day 38.

**Missed:**
- Proposed a redundant second fix ("always read critical data from leader")
  that's a blanket version of fix #1, without noticing the overlap until asked.
- When asked what Merchant B "gets" in plain English (not the term), repeated
  the term instead of the content ("possibly stale, never goes backward").

**Correction landed cleanly:** replaced permanent leader-pin with **log-position
tracking** as the cheaper mechanism, self-generated, once asked what's cheaper.

---

## Round 2 — New: Delivery Status Flicker (7.0/10)

*Order status polling shows delivered → in transit → delivered as reads bounce
between followers at different replication lag.*

**Landed:**
- Correct diagnosis and guarantee (monotonic reads), immediately.
- Correct final mechanism (log-position tracking).

**Missed — needed three prompts to get here:**
- Proposed a **2-second sticky window** (correctly borrowed from Round 1's
  read-your-own-writes fix) without noticing a delivery is tracked for
  20–40 minutes, not 2 seconds.
- Did not independently stress-test the mechanism; had to be walked through
  the concrete failure — sticky session expires, next poll lands on a
  *further-behind* follower, guarantee breaks — before recognizing why a
  time-boxed fix doesn't transfer from a one-shot write to a long-poll session.
- Once walked through it, correctly concluded log-position tracking has no
  such expiry gap because it isn't tied to time at all.

**The actual finding:** knowledge and diagnosis are solid; the gap is
**stress-testing your own proposed mechanism before being asked to.** Not a
consistency-models gap — a "does this fix survive the next question" gap,
which is precisely what the Day 40 multi-constraint drill tests.

---

## Round 3 — New: Post/Reply Ordering (9.0/10)

*User A posts an announcement; User B replies 30s later. User C's replica has
replicated the reply but not the post — sees the comment with no post to
attach to.*

**Landed, cold, no follow-up needed:**
- Asked one good clarifying question on an ambiguous brief instead of guessing.
- Correctly identified effect-before-cause and named causal consistency.
- Gave the exact mechanism taught on Day 36 — colocate causally-related writes
  in the same partition — from memory, unprompted.
- Stated the real cost unprompted: partitioning exists for load distribution;
  colocating causally-related data fights that goal directly.

**Best round of the bridge phase so far.** Matches the Day 36 material
(`day36-consistency-models.md`, Anomaly 3) almost exactly, recalled cold three
days later with no notes.

---

## Score Summary

| Round | Scenario | Score |
|---|---|---|
| 1 | Merchant refund / follower lag (re-run) | 8.5/10 |
| 2 | Delivery status flicker (new) | 7.0/10 |
| 3 | Post/reply ordering (new) | 9.0/10 |
| **Average** | | **8.2/10** |

**Gate cleared:** consistency ≥ 8/10 for Phase 3. Day 35's 5.0/10 fail on this
exact criterion is closed.

---

## What Changed Since Day 35

1. Vocabulary is now retrievable under pressure, not just recognizable —
   read-your-own-writes, monotonic reads, and causal consistency all named
   correctly, cold, without notes.
2. Costs arrive unprompted, attached to every proposal.
3. The capacity-vs-availability conflation (Day 35 Round 3, Day 38) **did not
   fire** when directly available as an easy wrong answer (Round 1's "why does
   permanent leader-read stop being affordable" question).
4. Cheaper mechanisms are now the default reach, not the fallback — log-position
   tracking was proposed unprompted in both Round 1 and Round 2.

## What Still Needs Work

**Stress-testing your own mechanism before the interviewer has to.** Round 2's
7/10 wasn't a knowledge gap — the correct guarantee and correct final mechanism
were both there immediately. The gap was proposing a fix and moving on, rather
than asking "does this actually hold for the full duration/scale of this
scenario?" before presenting it. This is a *different* skill from the Round 1–3
material and is exactly what Day 40's multi-constraint drill is designed to
test: whether a fix that's correct in isolation survives contact with the next
constraint.

---

## Next: Day 40 — Multi-Constraint Drill

Three scenarios with deliberately conflicting constraints. Gate: ≥7/10 to
reopen Phase 3 on Day 41/42 (pending — consistency gate now cleared, this is
the one remaining gate).
