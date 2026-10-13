# Foundations Review — Clusters 8-10

**Date:** 2026-10-13
**Status:** ✅ Clusters 8-10 complete, Cluster 11 next
**Format:** Cold, no notes — same as prior clusters.

---

## Cluster 8 — Microservices & Service Discovery (Days 11-12)

**Q1 (monolith → microservices trigger + shared-DB trap):** named general
microservices benefits (independent deployment, fault isolation, independent
scaling) correctly, but didn't initially answer the specific question —
what pain point in a *currently-working* monolith justifies the split.
Redirected toward Day 11's actual framing (team/organizational coordination
pain, not abstract "scale"), and landed a complete, well-reasoned answer:
teams blocked waiting on each other, bad-deploy blast radius forcing a full
revert, inefficient bulk scaling, and growing codebase bulk. Correctly named
the anti-pattern for split-code-shared-DB: **Distributed Monolith**, and
reasoned through its mechanics correctly unprompted (connection pool
exhaustion, row locks creating cross-service latency) before being asked.

**Q2 (service discovery):** correctly named the general mechanism (service
discovery, resolve by name not IP) but took three attempts to reach the
specific missing piece — **a registry must continuously health-check and
evict dead entries**, or it becomes actively worse than no registry (handing
out confident-but-dead addresses instead of failing fast). This piece
ultimately needed to be taught directly rather than retrieved. Good
follow-up question afterward, asked unprompted: does a recovered instance
get re-added automatically? (Yes — confirmed and explained: self-registration
plus health checks passing again.)

---

## Cluster 9 — CQRS & Event Sourcing (Days 15-16)

**Best cluster of the review so far — genuinely derived the pattern himself
through questioning rather than being told it.**

**Q1 (CQRS misconceptions):** correctly flagged "no joins on the read side"
as a misconception, but initially mis-defined CQRS itself as "no reads during
writes" (a real error — CQRS has nothing to do with temporal exclusion).
Corrected to the actual rule: separate write/read **models**, and the real
forbidden thing is **domain logic in queries**, not joins. Correctly
self-doubted a valid answer ("primary + read replica... I think this isn't
valid") — it was actually correct; same shape as
[[no_bottleneck_confidence_gap]], landing on the right answer without trusting
it. One more correction: CQRS is not "a microservices concept" — it applies
inside a monolith just as validly.

**Follow-up sequence (unprompted depth) — this is the standout part of the
session:** asked for a concrete before/after SalesPoint example, which
surfaced a specific EF Core question (navigation properties vs. foreign keys)
that reinforced the exact bloat problem CQRS solves. Then asked, sharply:
*"without an ORM, wouldn't disciplined raw SQL just naturally look like
CQRS already — what does the formal pattern actually add?"* This is an
excellent, non-obvious question. Answered precisely: yes, lightweight CQRS
(two classes, same DB) is a real, valid point on a spectrum; the formal
pattern's value is (a) codifying the "no domain logic in queries" rule as a
team-scale convention that survives turnover, not individual discipline, and
(b) describing how far the separation can go — all the way to a fully
separate, asynchronously-updated read store (which is where CQRS and event
sourcing's projections become the same conversation). **He then correctly
self-summarized the full spectrum** (same DB/no replicas → replica split →
fully separate async store) and confirmed it unprompted — strong synthesis.

**Q2 (event sourcing):**
- (b) snapshot + replay-only-since-snapshot — correct immediately, no
  correction needed.
- (a) correctly identified replaying creates latency, but initially didn't
  distinguish "querying one aggregate's history" (valid, fast, indexed) from
  "cross-aggregate reporting" (the real problem — event store is organized
  per-aggregate, a report needs to scan across all aggregates). Once
  distinguished, correctly derived the fix himself: **a projection**,
  maintained by an async worker consuming events — independently arrived at
  the same mechanism his own notes describe, matching the CQRS read-side
  conversation from Q1 exactly.
- Follow-up: asked whether the event store is "a log or a table" — good
  question, genuinely ambiguous from the notes. Clarified: physically a
  table, used in a strictly-append-only, ordered way; fast per-aggregate
  access comes from an index on `(aggregate_id, sequence_no)` — same
  left-prefix principle as Cluster 3's indexing material, not a different
  mechanism.

---

## Cluster 10 — Consistent Hashing, Sharding & Replication (Days 17-19)

Replication/leader-follower was already tested extensively in the bridge
phase (Days 39-42), so this cluster focused on consistent hashing's mechanism
and shard key criteria, with only a quick replication check at the end.

**Q1 (consistent hashing mechanism):** correctly diagnosed the modulo-hashing
problem (adding a node remaps almost every key) and the ring-based fix, but
described the affected region vaguely ("nearby nodes," plural). Sharpened to
the precise mechanism: a new node only takes over the single arc of keys
between itself and its **one specific predecessor** on the ring — every other
node's arc is completely untouched, which is *why* only ~1/N of keys move
(one slice splits into two; the other N-1 slices are unaffected).

**Q2 (bad shard key — `order_status`):** correctly identified the mutability
violation with a precise example (status changes would physically move the
row between nodes) — but inverted the rule's phrasing ("shard key must
**not** be immutable," meaning the opposite of the correct explanation that
followed — a [[vocabulary_precision_gap]] instance, phrasing inverted while
the underlying understanding was correct). Initially missed the second,
arguably bigger violation (low cardinality: only 5 possible values, capping
shards at 5 and guaranteeing skew) — once prompted, derived it himself with a
concrete, correct worked example (1M orders/year mostly settling on one
status → one massively hot node).

**Q3 (sync vs. async replication, quick check):** correctly named guarantees
and use-case mapping for both, and correctly named async's cost (staleness
window) — but initially stated only sync's guarantee, not its cost (the "name
the currency" gap recurring, Day 36). Once pushed, correctly named latency as
one cost — but described the failure case wrong ("if the follower is down,
primary data gets reverted"). Corrected: no revert happens; the write simply
**blocks/fails** because the required follower confirmation never arrives —
precisely CAP theorem's C-over-A tradeoff (Day 36, Cluster 4), re-surfacing
correctly once the wrong mental model (revert) was replaced with the right
one (block).

---

## Pattern Check

Two more [[vocabulary_precision_gap]] instances this session: an inverted
rule statement ("must not be immutable") and a wrong failure-mode guess
("reverted" instead of "blocked") — both cases where the *reasoning*
recovered correctly once gently corrected, consistent with every prior
cluster. Cluster 9 stands out as the strongest session of the whole review
so far — not just correct recall, but **independently-driven follow-up
questions that surfaced real, non-obvious understanding** (the raw-SQL-vs-
CQRS question in particular). Worth noting this as a genuine high point.

---

## Next: Cluster 11 — URL Shortener, Auth, Analytics, Feed, Autocomplete (Days 20-24)
