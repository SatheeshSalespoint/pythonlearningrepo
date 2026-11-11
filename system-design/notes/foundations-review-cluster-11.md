# Foundations Review — Cluster 11

**Date:** 2026-11-10 (first session back after an 18-day break)
**Status:** 🔄 In progress — Q1 done; long detour into distributed-systems
fundamentals (driven by his own questions); Q2 onward next session
**Format:** Cold scenario questions, same as prior clusters.

---

## Q1 — URL Shortener: user dashboard on a `short_url`-sharded table (Day 20)

**Scenario:** URLs sharded by `hash(short_url)`. Product asks for "show a user
all their short URLs, newest first."

**How it went:**
- First answer was right in spirit (user's URLs are scattered → latency) but
  vague on *which* shards. After the break, the mental model of sharding had
  drifted: pictured shards as separate tables (`Table_Shorturl_1..4`).
  Re-grounded: **one table, split across N servers, routed by
  `hash(key) % N`.**
- Claimed "user created 2 URLs → only 2 shards get hit." Corrected: the
  router only works *forward* from the shard key. Request carries only
  `user_id`, so it can't know which shards are empty → **scatter-gather to
  all shards**, latency = slowest shard, every shard does work per page view.
- Proposed composite key `hash(user_id + short_url)`. Tested it himself and
  correctly saw each different `short_url` → different hash → still
  scattered. Deeper reason: the dashboard request doesn't *have* a
  `short_url` at all.
- **Rule landed:** *a shard key only helps queries that carry its value.*
- Then (from re-reading Day 20, so not cold) found the strongest answer:
  the short URL is `base62(user_id) + base62(sequence)`, so **shard by
  `user_id` and decode it from the short URL on clicks** → both access
  patterns hit one shard. This is "embed the shard key in the ID"
  (Instagram-style IDs). **Day 20's notes contradict themselves here** —
  they rejected shard-by-user_id because "clicks would query all shards,"
  which isn't true given their own key format. (Correction note added to
  Day 20.)

**Push-backs and corrections:**
1. **Encode/decode as a bottleneck:** first turned a pure function into a
   separate network service — *creating* the bottleneck — then reversed it
   himself. Model answer: *Verdict: no bottleneck. Headroom: in-process CPU
   math, microseconds, scales with app servers. Risk: none worth designing
   for.* Same hesitation as [[no_bottleneck_confidence_gap]].
2. **Predictability:** said "nothing secret, so fine," then proposed UUIDs —
   which **break the design** (no user_id inside → can't route clicks; also
   36 chars). What's actually being accepted: link enumeration (finding
   links never shared publicly) and leaking per-customer volume. Middle
   ground: encrypt `user_id + sequence` with a server key before base62 —
   decodable by us, noise to outsiders.
3. **Cost of sharding by user_id:** correctly named **data skew** and
   **traffic skew** for a giant account. Refinements: traffic skew is mostly
   absorbed by the Redis cache (Day 20, ~99% hit); data skew is not.
   Sub-sharding giant accounts works but brings scatter-gather back for
   *their* dashboard — needs a small `user_id → sub-shard count` lookup
   table, cached on every app server. Shard key is `user_id`, not the whole
   short URL.
4. **Trusted user_id** comes from the validated JWT `sub` claim, never from a
   client-editable header.

---

## Detour (his questions) — distributed-systems fundamentals

### Does consistency matter for sharding?
Sharding alone doesn't create inconsistency — each row lives on one primary.
**Inconsistency comes from copies:** cache, read replicas, denormalized
dashboards, routing lookup tables. Bonus: sharding by `user_id` keeps one
user's transactions local (no cross-shard coordination).

### "How do you maintain consistency in a distributed architecture?" (asked in a real meeting)
His meeting answer had two correct techniques with imprecise framing:
- "Distributed = eventual consistency" → **No.** Distribution forces a
  *choice* (CAP), it doesn't force eventual.
- "Synchronous, everything completes before responding" → correct; name it
  (**sync replication** within a DB, **2PC** across services) and its cost
  (**latency + availability**).
- "Stick the user to the same DB for a few secs" → correct technique, but
  it's **read-your-writes consistency** — only the writer is guaranteed to
  see the write, not everyone.
- **Missing:** asking *"consistency of what?"* — replicas of one DB vs. data
  across services. Same "interrogate the brief" gap
  ([[assessment_weak_spots]]).

### Scale Cube — how DB scaling and microservices fit together
| Axis | Split | Examples |
|---|---|---|
| X — clone | identical copies | app instances, read replicas |
| Y — function | by what the code/data does | microservices, DB per service |
| Z — data | same table, by key | sharding |

Y decides *which* databases exist; then **each service's DB is scaled
independently** by its own load (Auth: replicas + cache; Merchant: nothing;
Transaction: sharded by merchant_id with replicas per shard; Reporting: CQRS
read DB fed by events). App instances and DB scaling are separate dials.
A service only touches its own DB.

### Saga (taught properly for the first time)
Saga had only ever been *mentioned* (Day 5 table row, Day 11 code snippet,
Day 14 pointer) — never taught. He asked whether it had been; it hadn't.
- **Mechanism:** chain of local transactions, one per service, each
  committing immediately; each step has a **compensating action** (business
  undo, not a rollback). On failure, compensations run in reverse.
- **Coordination:** orchestration (central coordinator, e.g. MassTransit
  state machine) or choreography (services react to events).
- **Guarantee → cost:** eventual consistency, in-between states visible;
  costs complexity (an undo per step, idempotency everywhere), buys
  availability (no cross-service locks).
- **Bridge that made it click:** Saga = the event-driven choreography he has
  built in real work **+ failure events that trigger each service to undo
  its own part.** Needed only when an earlier step must be reversed (money,
  stock, seats) — not when later steps can just be retried.
- **Orchestration/choreography is general**, not Saga-only (e.g. Temporal /
  Durable Functions workflows; fan-out events with nothing to undo).
  Name collision: Kubernetes "orchestrator" (Day 12) is a different meaning.

### Outbox (confirmed + corrected)
- Correction: business write and outbox row must be in **one local
  transaction**, not "commit, then write outbox."
- Relay drains pending rows to the broker. Publish-then-crash-before-mark →
  duplicate → **at-least-once**, so consumers must be idempotent. (Day 26
  notes said "exactly-once" — corrected there.)
- Why a broker, not direct calls: messages wait while a consumer is down.

### Outbox vs. Saga — the confusion and its resolution
He first summarized them as alternatives ("Outbox writes to DB, no undo;
Saga publishes without DB, has undo"). Corrected: **they answer different
questions and are used together.** Outbox = *will my event definitely be
sent?* (delivery, one service). Saga = *if a later step fails, how do I undo
earlier ones?* (business consistency, many services). Saga steps still write
to their own DB and use Outbox (with its relay) to hand off.

**His final version (tightened):**
> **Saga:** coordinates a workflow across services — each step a local
> transaction; on failure, earlier steps run compensating actions.
> **Outbox:** inside one service — business change + event in one
> transaction; a relay publishes it so it's never lost. Saga steps use it.

---

## Pattern Check

- **Vocabulary precision gap, again** ([[vocabulary_precision_gap]]): "table
  shards" for shards, "joined" for merged, "sub-sharding" without naming its
  cost, Outbox/Saga as alternatives instead of layers. Each time, the
  reasoning recovered once corrected.
- **Rust after the break:** the shard-routing model had drifted (separate
  tables, "only 2 shards"). A worked example with concrete hash values fixed
  it quickly — [[teaching_unfamiliar_topics]] applies to rusty topics too.
- **Strong signal:** he drove most of the session with his own questions
  (consistency, scale cube, Saga, orchestration scope), and kept pushing on
  Saga until it genuinely clicked rather than accepting a fuzzy picture.

---

## Open Questions — carry over to next session

> **Update 2026-11-11:** items 1 and 2 closed in `foundations-review-cluster-11-part2.md`; its "Still Open" list supersedes this one.

1. **Saga:** what if a compensation (the refund) itself fails?
2. **Scale cube:** which axis/service for: (a) Transaction Service CPU 95%,
   shards fine; (b) Auth replicas 90% CPU on token lookups; (c) one
   Transaction shard's primary saturated by a giant merchant's writes?
3. **Saga:** in his past event-driven work, which step would have needed a
   compensating action?
4. **Q2 (Auth, Day 21):** token stolen, logout at 10:00 (Redis DEL), Redis
   crashes 10:05, fallback = local JWT validation, attacker request at 10:06
   — what happens, what is that choice called (fail open vs. fail closed /
   AP vs. CP), which for fintech, and what does each cost?
5. Then Q3-Q5: Analytics (Day 22), Feed (Day 23), Autocomplete (Day 24).
