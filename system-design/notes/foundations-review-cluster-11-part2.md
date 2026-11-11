# Foundations Review — Cluster 11, Part 2

**Date:** 2026-11-11
**Status:** 🔄 Cluster 11 still in progress — open questions from Part 1
mostly closed; Q2 (Auth) next
**Previous:** `foundations-review-cluster-11.md` (Part 1, 2026-11-10)

Started with two of his own questions from real (POS / sales) work, then
worked through Part 1's open questions.

---

## His question 1 — Showing a sale that spans Sale, Payment, Inventory

**Setup:** Sale Service, 3 instances, sharded by `merchant_id`, primary +
replica. A sale references payment and inventory IDs. "To show a sale, do I
make three calls and merge on the app side?"

**Answer: not from the app — and for a sale, usually not three calls at all.**

First decide what the sale *owns*: is the data a **fact about the sale at
that moment** or **the current state of something else**?

| Data | Owner |
|---|---|
| Line items, qty, price at time of sale, product name | **Sale** (history) |
| Payment method, amount, last 4 | **Sale keeps a copy** (fixed once paid) |
| Payment status (refunded/disputed) | **Payment Service** (changes later) |
| Current stock level | **Inventory Service** (not needed for a receipt) |

Three options:
1. **Snapshot at sale time (recommended)** — store everything the receipt
   needs; one call, one shard. Cost: duplicated storage; changeable fields
   (refund status) updated via events (Outbox → broker). For a receipt,
   copying isn't a compromise — it's the correct model.
2. **Server-side API composition** — Sale Service / BFF / gateway calls the
   others **in parallel** and merges. Never the app: mobile latency ×3, app
   coupled to internal service layout. Cost: latency (slowest call),
   availability (need a partial-response plan).
3. **CQRS read model** (Day 15) — for list/search screens spanning services.
   Cost: complexity, eventual consistency.

Scaling setup only routes the call (LB → any instance →
`hash(merchant_id)` → shard → replica). Catch: reading a just-created sale
from a lagging replica → **read-your-writes**: read from primary briefly
after the write.

**Check answered correctly:** a renamed product → old receipts show the
**old name**, so product names belong in the sale snapshot.

---

## His question 2 — Adding a new field to snapshots (schema evolution)

**Not previously taught** — introduced from scratch.

**Deciding question:** *could the value have been different at sale time?*
- Never changes (barcode, SKU) → filling old records with today's value is
  truthful.
- Can change (category, tax rate, promo) → filling with today's value
  **rewrites history**.

Options:
1. **Optional field + tolerant reader** (default) — new records have it, old
   don't; readers accept missing/unknown fields. Cost: one "if missing"
   check. Use when the value can change — blank is more honest than a guess.
2. **Backfill** — one-off job filling old records. Only for never-changing
   fields. Per shard, small batches, off-peak, throttled; writes hit the
   **primary** (capacity) and increase replica lag; must be idempotent and
   resumable.
3. **Versioned snapshot** — `snapshot_version` field; **upcast** old shapes
   to new in code on read. Cost: complexity. Use for renames/splits/meaning
   changes, not simple additions.

**Rolling-deploy trap:** with 3 instances, old and new code run side by side
during a deploy. Safe order is **expand → migrate → contract**: first deploy
readers that tolerate both shapes, then writers that write the new field
(+ backfill if valid), only later drop old-shape support. Same rule for
events in the broker.

---

## Open Q1 (from Part 1) — Saga: the compensation (refund) fails

**His answer:** retry; if still failing, publish a failure event, cancel the
order, email the customer "refund in a few hours"; customer sees "Pending."

**What was right:** retry, then communicate.

**Corrections:**
1. **How to retry money safely:**
   - **Idempotency key** (`refund_id`) — a timed-out request may have
     succeeded; retrying without a key risks a **double refund**.
   - **Exponential backoff + jitter**, plus a **circuit breaker** (Day 13).
   - **Durable retry** — a `refund_requests` row (status PENDING) worked by
     a background worker, so restarts don't lose it (same idea as Outbox).
2. **Publishing a failure doesn't return the money.** Rule: **a
   compensation must never be allowed to permanently fail** — there's no
   "undo the undo." Temporary failure → keep retrying durably. Permanent
   failure (card closed) → **DLQ + alert + human** (bank transfer, store
   credit). The last line of defence is a person.
3. **Customer status contradicted itself** — cancelled the order, then said
   it shows "Pending." Inventory already failed, so show **honest
   intermediate states**: *Cancelled — refund in progress* → *Cancelled —
   refunded* / *refund needs attention*. Don't promise "a few hours" —
   say "being processed" and notify on completion. Visible in-between
   states are Saga's cost; design them deliberately.

---

## Open Q2 (from Part 1) — Scale cube: match symptom to axis

First time meeting these diagnoses, so **taught the method first, worked
Symptom 1, then he did 2 and 3** ([[teaching_unfamiliar_topics]] — worked
well).

**The method — two questions:**
- **A:** What's overloaded? App tier, or DB — and if DB, reads or writes?
- **B:** Which fix matches?

| Overloaded | Fix | Axis |
|---|---|---|
| App instances (CPU) | Add instances (stateless) | X |
| DB reads | Cache first, then replicas | X |
| DB writes on one primary | Dedicated shard, then sub-shard | Z |
| Service doing unrelated jobs | Split the service | Y |

**Symptom 1 (worked by me):** Transaction Service CPU 95%, shards fine →
app tier → add instances / autoscale. Watch DB **connection counts**
(instances × pool size per shard) and check whether code is the real cause.

**Symptom 2 (his — correct):** replicas overloaded by reads → add replicas;
cost money/capacity; check query optimisation first (good instinct).
Additions:
- **Cache first:** token lookups are hot, tiny, rarely change → Redis.
  Day 21 already caches tokens, so DB load means asking *why are lookups
  missing the cache?*
- **Missed cost — consistency:** every copy (replica or cache) is a place a
  just-revoked token can still look valid (replica lag). Leads into Q2 Auth.

**Symptom 3 (his — correct diagnosis and fix):** primary write-saturated by
a giant merchant → sub-shard. Sharpened:
- **Why replicas don't help** is mechanical, not "consistency": in
  single-leader replication only the primary takes writes and **every
  replica applies the same writes**. (His consistency point applies to
  multi-leader, a different idea.)
- Sub-sharding makes **writes faster**; only that merchant's
  cross-sub-shard reads become scatter-gather — results are **merged**, not
  joined (vocabulary, again).
- **Try a dedicated shard first** — no scatter-gather, frees neighbours;
  sub-shard only if one big machine can't keep up. Both use the
  `merchant_id → shard(s)` lookup table.

---

## Pattern Check

- **Asked to be taught rather than guessing** on the scale-cube symptoms
  ("first time facing these") — then, given the method, answered 2 and 3
  correctly with only refinement needed. Method-first worked.
- **Vocabulary precision** ([[vocabulary_precision_gap]]): "joined" for
  merged (second session in a row); "consistency" offered as the reason
  replicas don't help writes when the reason is mechanical.
- **Stress-testing his own answer** ([[assessment_weak_spots]]): the Saga
  answer cancelled the order *and* showed "Pending" — a self-contradiction
  he didn't catch.
- **Strong signal:** brought two real problems from his own domain (sale
  snapshots, schema evolution) — applying the material to work, not just
  answering drills.

---

## Still Open — next session

1. **Tax-rate check:** adding "tax rate applied" to sale snapshots — backfill
   old sales with today's rate? What should the app show for old sales?
2. **Saga in his past work:** which step would have needed a compensating
   action?
3. **Q2 (Auth, Day 21):** token stolen, logout 10:00 (Redis DEL), Redis
   crash 10:05, fallback = local JWT validation, attacker at 10:06 — what
   happens, what is the choice called (fail open vs fail closed / AP vs CP),
   which for fintech, and costs.
4. Then Q3–Q5: Analytics (Day 22), Feed (Day 23), Autocomplete (Day 24).
