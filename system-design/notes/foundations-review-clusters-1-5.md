# Foundations Review — Clusters 1-5 (Phase 2.75)

**Dates:** 2026-09-24 (Cluster 1), 2026-09-30 – 2026-10-01 (Clusters 2-5)
**Status:** ✅ Clusters 1-5 complete, Clusters 6-14 remaining
**Format:** Cold, no notes — scenario questions over Days 1-19 lecture material,
never previously scenario-tested. Requested by the user after Day 42, feeling
some early concepts (e.g. Redis recovery) were shaky despite being marked done.

---

## Cluster 1 — Scalability & Load Balancing (Days 1-2)

**Landed:** Good real-world instinct to diagnose before scaling (stateless
check, response-time profiling, DB tuning) — genuinely senior behavior, not
asked for but volunteered. Correctly reasoned vertical scaling's real risk is
**downtime during resize, not just a hard ceiling** — better answer than
expected. Eventually landed both fixes for the session-affinity problem:
shared store (Redis) and self-contained tokens (JWT), with correct
guarantee/cost framing on each once prompted (JWT: no per-request lookup, but
can't revoke early without reintroducing some shared state).

**Corrected in-session:**
- "Scale down" → should be **"scale out"** for horizontal.
- "Cost wise more effective" (horizontal) was money-only framing — the real
  currency is **complexity** (distributed coordination), same lesson as Day 36
  now transferring to Day 1 material.
- "OAuth" → the mechanism being described was **JWT**; OAuth is a broader
  authorization protocol, not the token format itself.
- Correctly self-scoped an answer to "what happens" without volunteering
  remedies he wasn't asked for yet (a good discipline, not a gap).

---

## Cluster 2 — Caching & CDN (Days 3, 9)

**Landed:** Cache-Control policy question (public vs. private/no-store) was
clean on the first try, including the security reasoning. Correctly connected
the write-through cache cost to the **dual-write problem** named back on
Day 38 — good transfer, recognizing the same shape across different system
pairs (DB+broker there, DB+cache here).

**Corrected in-session:**
- CDN staleness fix was muddled ("pass Cache-Control header" doesn't reach
  already-cached edge copies) — landed on the real mechanism
  (**content-hashed filenames**, new content → new URL → automatic cache
  miss, no invalidation needed) once pointed at his own aside.
- Write-through's cost was initially stated backwards (described the
  *alternative's* risk, not write-through's own cost) — corrected to the
  actual cost: partial failure between two systems being written to.

---

## Cluster 3 — Databases & Indexing (Days 4, 10)

**Landed:** Left-prefix rule (Q2) was correct and clean from the start, both
for the working query and the broken one. CAP-adjacent reasoning was strong
throughout. Good habit spotted: asked "have you explained me this before?"
rather than assuming — verified against notes before answering, found it
genuinely was taught (Day 10) and re-explained moments earlier in-session —
then gave a correct restatement in his own words afterward.

**Corrected in-session:**
- SQL vs. NoSQL verdict initially self-contradicted (catalog → MySQL, then
  later catalog → MongoDB) — resolved by tying back to the stated
  requirement (catalog needs joins with orders/merchants → SQL).
- N+1 query problem was attributed to NoSQL here (carries into Cluster 5,
  see below) — should have been framed as a general data-fetching pattern.
- Functions-on-indexed-columns and OFFSET pagination were both genuinely
  unknown (`WHERE YEAR(created_at) = 2026` defeats the index; `OFFSET`
  requires scan-and-discard, growing linearly with page depth) — taught
  mechanism-first (index = value-seek structure, not a position-jump
  structure), then correctly restated in his own words after one nudge.
- One real edge-case test of his own: tried adding a WHERE filter *alongside*
  OFFSET, asking whether that fixes it — correctly shown that OFFSET's cost
  persists regardless of what's added alongside it; true cursor pagination
  **replaces** OFFSET, not supplements it.
- Good follow-up question: does the server remember the pagination cursor,
  or must the client resend it? Answered and explicitly connected back to
  Cluster 1's statelessness principle (client carries the cursor, same
  reason JWTs beat server-side session storage).

---

## Cluster 4 — CAP Theorem (Day 5)

**Landed — strongest cluster of the five.** All three questions answered in
the guarantee/mechanism/cost shape *unprompted*, matching the bridge-phase
discipline exactly: payment → CP, synchronous cross-region write, cost named
explicitly as latency, accepted deliberately. Feed → AP, eventual consistency,
with an unprompted sophistication — recognizing the guarantee should
strengthen specifically at the "complete the sale" moment, which is the
Day 23 Instagram differential-consistency pattern resurfacing cold, unprompted.
Q3 (per-operation CAP choice) answered with concrete, correct SalesPoint
examples on both sides.

**Corrected in-session:** the "why can't you opt out of P" reasoning was
thin — added that partition isn't a design choice, it's a physical fact of
distributed systems (network links fail/drop regardless of what you design);
the real choice is only what the system does *when* it happens.

---

## Cluster 5 — API Design (Day 6)

**Landed:** Correct tool selection on all three (REST for the cacheable
public API, gRPC for internal service-to-service, GraphQL for the flexible
mobile dashboard) — GraphQL's reasoning (fetch exactly what's needed, no
over/under-fetching) was solid from the first answer. Correctly named
**DataLoader** as the standard N+1 fix. After correction, gave a precise,
separated two-part answer for gRPC's speed: Protobuf's compact binary wire
format (serialization speed) vs. the `.proto` contract's compile-time type
enforcement (correctness) — plus volunteered HTTP/2 multiplexing as a third,
distinct benefit.

**Corrected in-session:**
- REST's CDN-cacheability reasoning was initially just "these two words" —
  sharpened to the actual mechanism: HTTP caching keys on URL+method, and a
  single GraphQL endpoint gives a CDN nothing to distinguish requests by.
- gRPC's speed reasoning was initially one blurred claim ("streams better,
  reduces latency") — needed prompting to separate wire-format efficiency
  from compile-time type safety as two distinct benefits.
- **N+1 mislabeled as GraphQL-specific** (continuing the Cluster 3 pattern,
  where it was mislabeled as NoSQL-specific) — corrected to: it's a general
  data-fetching pattern, GraphQL just makes it easy to write by accident
  because each field resolver runs independently by default.

---

## Recurring Pattern Across All Five Clusters

**Conceptual understanding is consistently solid — the gaps are almost
entirely in (a) precise vocabulary and (b) answering the literal question
asked rather than an adjacent one.** Concrete instances:

- Vocabulary slips: "scale down" for scale-out, "OAuth" for JWT, N+1
  attributed to the wrong technology twice (NoSQL, then GraphQL) instead of
  named as a general pattern.
- Question drift: Cluster 1 Q1 ("name the two scaling approaches") was
  answered with "how to decide whether to scale at all" — a good answer to a
  different question. Cluster 3's cost statement for write-through described
  the *alternative's* risk rather than write-through's own cost.
- **Every single correction landed immediately and stuck** — nothing needed
  repeating across clusters, and cross-cluster transfer happened unprompted
  multiple times (Day 36's "name the currency" lesson reapplied to Day 1
  material; Day 38's dual-write problem re-recognized in a cache context;
  Day 23's differential consistency resurfacing in the CAP cluster; Cluster 1's
  statelessness principle re-applied to pagination cursors in Cluster 3).

This matches the exact shape found across the bridge phase (Days 36-42): rough
on first contact with precision, but the corrective loop is fast and reliable,
and concepts genuinely transfer across contexts rather than staying siloed per
topic.

---

## Next: Cluster 6 — Message Queues & Event-Driven Architecture (Days 7, 14)
