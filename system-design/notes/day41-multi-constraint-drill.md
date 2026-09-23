# Day 41: Multi-Constraint Drill

**Date:** 2026-09-18 (Round 1) / 2026-09-23 (Rounds 2–3, resumed after a
production-issue break)
**Duration:** ~70 mins total, across two sittings
**Status:** ✅ Complete — gate cleared
**Phase:** 2.5 Bridge (Days 36–42)
**Format:** Cold, no notes — three scenarios, each requiring two or more
constraints to be crossed, not solved in isolation
**Overall Score:** 7.33/10
**Gate:** Multi-constraint ≥ 7/10 for Phase 3 — **PASSED**

---

## Why this day exists

Day 35 Round 5 scored 4.0/10 — the second of two failed criteria blocking
Phase 3. The finding: constraints were worked correctly *in isolation* but
never *crossed*. This is the direct re-test.

---

## Round 1 — Order storage: cost × residency (7.0/10)

*8,000 merchants, 7-year retention, $2,000/month budget, NZ/AUS residency,
90-day sub-second retrieval SLA.*

**Landed:**
- Self-corrected two real errors immediately once flagged, no defensiveness:
  (1) treated an indexed point-lookup on 36M rows as "a challenge" — a
  manufactured bottleneck, same shape as Day 40 but inverted (talking
  himself *into* a problem instead of out of a real one); (2) called
  residency's requirement "replication," when residency is the *opposite* of
  replication — two disjoint datasets, never copied across the border (same
  mistake as Day 35 Round 5).
- Correctly identified, once prompted, that residency forces **two separate
  infrastructure deployments** (not just double storage) — the real crossing
  insight for this scenario.
- Asked a good clarifying question on an unstated NZ/AUS merchant split
  instead of guessing silently.

**Missed:**
- Never opened with the standing drill question unprompted (had to be asked
  a second time).
- Could compute both halves of a crossed constraint (storage cost, instance
  floor cost) but needed direct help assembling them into one verdict —
  packaging, not reasoning.
- Numbers here turned out to comfortably fit the budget (5.9× headroom) —
  this round tested whether he'd force a fight where there wasn't a tight
  one; he didn't, which is correct, but the round didn't stress-test a real
  squeeze (that came in Round 2).

---

## Round 2 — Fraud scoring: cost × latency (8.0/10) — best round

*50,000 tx/sec peak, $0.002/call third-party fraud API, $5,000/month budget,
200ms hard SLA.*

**Landed:**
- Caught his own 10× arithmetic error unprompted mid-recalculation (500/sec
  vs. the 5,000/sec he'd first written) — same "lost a zero" pattern flagged
  since Day 22/33/38, but this time self-caught, not flagged by me.
- **Correctly challenged the brief's ambiguity** — treating "peak" as sustained
  for a full 24 hours — and replaced it with a stated, defensible assumption
  (4 hours of true peak) without being told to. This is the exact standing
  drill from Day 35 ("what am I taking as given that I should challenge?"),
  demonstrated unprompted for the first time this bridge phase.
- Reached the real verdict — **$4.1M/month vs. a $5,000 budget, an ~820×
  overshoot** — and stated it as a clean, unconditional "doesn't fit," no
  hedging. Direct contrast with Day 40 Round 1's four-attempt hedging loop on
  a "no bottleneck" verdict; here, a genuinely bad verdict was delivered just
  as cleanly as a good one.
- Independently proposed the correct fix (tiered fraud scoring: cheap
  in-house rules on 99.88% of transactions, expensive model reserved for the
  0.12% that fits budget) once taught the mechanism.

**Missed:**
- The *cost* of the tiered-fraud-scoring fix took three attempts to land on.
  First two attempts named technical costs (latency, infra scaling) instead
  of the actual cost: **decision-quality degradation** — real fraud that the
  accurate model would have caught now slips through the cheap rules, a
  business risk, not an engineering one. Once stated plainly, he immediately
  recognized the "hand this back to the business with its cost attached"
  move from Day 35 Round 5 and applied it unprompted.

---

## Round 3 — Inventory alerts: consistency × residency (7.0/10)

*Cross-location stock alerts, 5-second SLA, zero overselling, NZ/AUS
residency for dual-region merchants.*

**Landed:**
- Identified the sharp conflicting pair **fast and correctly, on the first
  read** — dual-region merchants force cross-border coordination for both
  the alert aggregate and the overselling lock, and residency forbids
  exactly that. Faster than Round 1's equivalent moment.
- Explicitly said, unprompted: *"I don't want to save NZ merchant data in
  AUS and vice versa"* — correct instinct that residency shouldn't bend.
- Once corrected and taught the pool-splitting + periodic-reconciliation
  pattern, converged immediately and gave a complete, correctly-shaped final
  answer: consistency stays strong *within* each region's own allocated
  slice, the cross-region total is only eventually consistent, and the cost
  explicitly named **lost sales** (a business-facing cost) alongside the
  infra cost — not just the infra cost alone.

**Missed — the actual finding of the round:**
- When forced to pick which constraint bends, **he first picked the one he
  had just correctly said shouldn't bend** — proposed cross-replicating
  merchant data between NZ and AUS to "guarantee consistency," directly
  contradicting his own prior statement. This is a real, specific failure
  mode: reasoning correctly in analysis mode, then reverting under the
  pressure of having to commit to a design. Distinguishing *negotiable*
  constraints (a UX target, a risk tolerance) from *non-negotiable* ones (a
  legal/compliance boundary) is understood in the abstract but doesn't yet
  survive the moment of choosing a design.

---

## Score Summary

| Round | Scenario | Score |
|---|---|---|
| 1 | Order storage — cost × residency | 7.0/10 |
| 2 | Fraud scoring — cost × latency | 8.0/10 |
| 3 | Inventory alerts — consistency × residency | 7.0/10 |
| **Average** | | **7.33/10** |

**Gate cleared: multi-constraint ≥ 7/10.** Combined with Day 39's consistency
gate (8.2/10), **both Phase 3 gates are now met.**

---

## What Changed Since Day 35 Round 5 (4.0/10)

1. **Constraints are now crossed, not just computed separately** — every
   round correctly combined two constraints into one number (storage + instance
   floor cost; transaction volume + per-call pricing; regional consistency +
   residency), where Day 35 handled each constraint in isolation.
2. **Challenging the brief happened unprompted, for the first time** — Round
   2's "is 24-hour sustained peak realistic?" was self-initiated, not asked
   for. This is the single standing drill from Day 35 that hadn't
   generalized until now.
3. **A genuinely bad verdict was delivered as cleanly as a good one** — the
   $4.1M/$5K overshoot was stated flatly, no hedging, extending Day 40's
   "no bottleneck" confidence work to "yes, this is badly broken" confidence.
4. **The business-facing cost/tradeoff instinct (Day 35 Round 5's "hand it
   back with the cost attached") is starting to fire unprompted**, though
   still needs the specific cost pointed out first before he generalizes it
   within the same round.

## What Still Needs Work

**Committing to a design under pressure doesn't yet match the reasoning done
moments earlier.** Round 3's core finding: correctly reasoned that residency
is non-negotiable, then proposed violating it anyway the moment a design
commitment was required. The gap isn't understanding *which* constraints are
negotiable — it's that recognizing this in analysis and holding it while
actually choosing a design are still two different skills for him. Worth
watching specifically in Phase 3, where hard systems (starting with Uber)
will require committing to designs under exactly this kind of pressure.

---

## Bridge Phase Complete

| Gate | Day | Score | Status |
|---|---|---|---|
| Consistency ≥ 8/10 | Day 39 | 8.2/10 | ✅ Cleared |
| Multi-constraint ≥ 7/10 | Day 41 | 7.33/10 | ✅ Cleared |

**Next: Day 42 — Round 6 (real-time/strong consistency) + full six-criteria
re-assessment. Phase 3 (Uber) opens Day 43 if Day 42 confirms readiness.**
