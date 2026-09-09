# Day 36: Consistency Models (Mechanism-First)

**Date:** 2026-09-09
**Duration:** ~45 mins
**Status:** ✅ Complete
**Phase:** 2.5 Bridge (Days 36–40)
**Format:** Teaching day — mechanism and worked examples first, testing deferred to Day 38
**Checks:** 3/3 correct, with one framing relapse (see below)

---

## Why This Day Exists

Day 35 Round 3 scored 5.0/10 — the weakest round of the checkpoint. Two of three
proposed fixes for *replication lag* were actually *failover* fixes, and one of
them (multi-leader) makes consistency worse. Root cause: the working model was
**"critical tables get strong consistency, non-critical get eventual"** — Day 19's
model, and too coarse to reason with.

This day replaces that model.

---

## The Frame

> A consistency guarantee is a promise about **what a reader is allowed to
> observe**. It is not a property of the data. It is a property of the
> relationship between a **reader** and a **write**.

Every guarantee below is defined identically: *"this specific anomaly cannot
happen to you."* Learn the anomalies and the guarantees come free.

## The Setup — every anomaly comes from this one picture

```
        writes              async replication (lag L ~ 400ms)
Client ────────▶ LEADER ──────────┬──────────▶ Follower A
                                  └──────────▶ Follower B

Reads go to whichever follower the load balancer picks.
```

**Nothing is broken.** No failover, no outage, no partition. This is the system
working normally. Every anomaly below is a consequence of healthy async
replication — which is why failover fixes do not address any of them.

---

## Anomaly 1 — Your Own Write Vanishes

```
t=0ms    Merchant issues a refund       → LEADER   ✅ saved
t=50ms   Dashboard reloads              → Follower B (lag 400ms)
                                          refund not there yet
t=50ms   Merchant sees: no refund       😱 "did it fail? click again?"
t=400ms  Refund appears
```

The most damaging anomaly, because the user **knows** what should be there.

**Guarantee: read-your-own-writes** (read-after-write)
> *Any write you made yourself will be visible to you on any subsequent read.*

Scope is **you**. It says nothing about any other reader — the point missed in
Day 35 Round 3(c).

### Three implementations

| How | Mechanism | Cost |
|---|---|---|
| Recently-written → leader | "Written in the last 5s? → leader" | Leader takes load; lose read scaling on hot keys |
| **Sticky session** | Pin *this merchant* to the leader ~2s after their write | Session state; uneven follower load |
| **Log position tracking** ⭐ | Write returns `LSN=8842`; client sends it on the next read; router picks a follower that has applied ≥ 8842 | Client/router complexity — most precise, no wasted leader traffic |

The third is what production systems do (MySQL GTIDs, Postgres LSNs). Naming it
is the difference between having read a blog post and having run this.

---

## Anomaly 2 — Time Runs Backwards

A **different** merchant, who wrote nothing:

```
t=500ms  Reads balance → Follower A (caught up)   sees $4,200 ✅
t=900ms  Refreshes     → Follower B (lagging)     sees $4,700 😱
```

Nothing is corrupt — each value was true at some point. But the balance moved
**backwards in time**, which reads as a bug.

**Guarantee: monotonic reads**
> *You may see stale data. You may never see data get **more** stale than what
> you already saw.*

**Implementation:** hash `merchant_id` → follower. Same user, same replica, so
their view only moves forward.

**Cost: almost nothing.** Uneven load, plus a one-time backwards jump if that
replica dies and the user reroutes.

### This is the Day 35 Round 3(c) answer

The second merchant made **no write**, so:
- read-your-own-writes does not apply — there are no "own writes"
- sticky-to-leader has no trigger to fire on
- the needed guarantee is **monotonic reads**, and it is nearly free

The instinct was to reach for the expensive fix; the correct fix was cheaper
*and* the expensive one would not have worked.

---

## Anomaly 3 — The Effect Arrives Before the Cause

```
Merchant writes, in order:
  W1: refund $500 on invoice #77
  W2: note on invoice #77 — "refunded per customer request"

Different partitions, different lag. An accountant reading sees:
  ✅ note: "refunded per customer request"
  ❌ invoice #77: no refund
```

The note explains a refund that, to the reader, never happened.

**Guarantee: consistent prefix reads** (the readable core of **causal consistency**)
> *If W1 happened-before W2, nobody sees W2 without W1.*

**Implementation:** keep causally-related writes in the **same partition** so they
share an ordering, or track dependencies explicitly with version vectors.

**Cost:** a real constraint on the partitioning scheme — and partitioning is
normally chosen for load distribution, so the two goals fight. Version vectors
are the alternative, at the price of per-write bookkeeping.

Bites hardest in **event-driven systems** (Days 14, 29): two topics, two
consumers, two lag profiles, effects observed before causes.

---

## Anomaly 4 — Two Observers Disagree About *Now*

```
Same instant, same balance:
  Accountant   → Follower A → $4,200
  Store owner  → Follower B → $4,700
```

Both on the phone to each other. There is no story where both are right.

**Guarantee: linearizability** (what people usually mean by "strong consistency")
> *The system behaves as if there is exactly one copy of the data, and every
> operation takes effect atomically at one instant. Once a write completes, every
> subsequent read — by anyone — sees it.*

**Implementation:** synchronous replication, consensus (Raft/Paxos), or route all
reads to the leader.

**Cost — say this out loud in an interview:**
1. **Write path:** every write pays an extra network round trip.
2. **Under partition:** availability drops — a slow or dead follower **blocks
   writes**. You chose C, so you gave up A. This is CAP in its purest form.

---

## The Hierarchy

```
Eventual consistency          ← baseline; only promise is "converges eventually"
        │
        ├── Session guarantees ── SIBLINGS, not a chain; pick the ones you need
        │     • read-your-own-writes    (your writes visible to you)
        │     • monotonic reads         (never go backwards)
        │     • monotonic writes        (your writes applied in your order)
        │     • writes-follow-reads     (write after read → ordered after it)
        │
Causal consistency            ← the above, plus cross-user cause→effect ordering
        │
Linearizability               ← one copy, one timeline, everyone agrees
```

Cost climbs and **availability falls** as you descend. The four session
guarantees are cheap and cover ~90% of real user-facing problems.

---

## The Decision Procedure ⭐ (memorise this)

1. **Who is the observer?** The writer? A different user? A downstream service?
2. **What anomaly would they actually notice?**
   vanished own write / backwards / effect-before-cause / two people disagreeing
3. **What is the cheapest guarantee that prevents *that* anomaly?**

### Applied to SalesPoint

| Operation | Observer | Anomaly they'd notice | Guarantee | Cost |
|---|---|---|---|---|
| Merchant refunds, checks own dashboard | the writer | own write vanished | read-your-own-writes | sticky ~2s, or LSN |
| Another merchant views shared balance | non-writer | balance jumps backwards | monotonic reads | ~free, pin to replica |
| Refund + explanatory note | third party | note without refund | consistent prefix | same partition |
| Payment authorisation | the system | double-spend | **linearizable** | latency + availability |
| Yesterday's report | anyone | none — it's yesterday | eventual | free |

**Five rows, five different answers, one database.** That is what "consistency is
not a property of tables" means in practice.

---

## Comprehension Checks (3/3)

**Q1 — Merchant updates address, immediately sees the old one.** ✅
Read-your-own-writes violated; cheapest fix is a ~2s sticky session.

**Q2 — Does the nightly reconciliation job need read-your-own-writes?** ✅
No — the job is not the writer, so there are no own writes to be consistent with.

*Extension:* it does need something else — a **complete** view up to the day
boundary. Reading a follower lagging 30s at 11pm silently drops the 10:59:30
transactions, which resurface tomorrow as false mismatches. That is a
**freshness requirement**, not a consistency guarantee: wait until the follower
has applied everything past midnight, then read. On a reconciliation job it is a
correctness bug, not a UX annoyance.

**Q3 — Cost of making everything linearizable?** ✅
Both costs named correctly: latency on the write path, availability lost when a
follower is slow or down.

---

## ⚠️ The Relapse to Watch

Q3's answer opened with:

> *"Transactions, profiles, user account events can be linearizable. But other
> data which were non critical is not need."*

**That is the old model returning** — sorting data into critical / non-critical
buckets, exactly the Day 19 framing that produced the Round 3 failure.

Test it on the given example — **a merchant updating their profile**:
- Important data? Yes.
- Needs linearizability? **No.**
- What anomaly would anyone actually notice? Exactly one: the merchant saves the
  address and sees the old one. That is **read-your-own-writes**.
- Does any *other* merchant care about seeing the profile 400ms late? No.

Important data, and the correct guarantee is a **2-second sticky session** —
nearly free — not synchronous replication taxing every write.

**Payment authorisation is different for a specific reason:** two concurrent
authorisations against the same balance can both succeed and overdraw the
account. That is a **double-spend** — not about what a user *observes*, but about
the system reaching a wrong state.

> **Reach for linearizability when concurrent writers can corrupt state, not when
> the data feels important.**

This is the specific habit Day 38 re-tests.

---

## Key Takeaways

1. Consistency is about the **reader↔write relationship**, never about tables.
2. Every anomaly here comes from **healthy async replication** — failover fixes
   address none of them.
3. **Monotonic reads is the cheap guarantee that gets overlooked** — it covers
   non-writers, and it is nearly free.
4. Session guarantees are **siblings**, not a ladder. Pick the ones you need.
5. Linearizability is for **state corruption by concurrent writers**, not for
   important-feeling data. It costs a round trip per write and your availability
   under partition.
6. **Freshness ≠ consistency.** A batch job may need "caught up past midnight"
   without needing any consistency guarantee at all.

---

## Next: Day 37 — Search Engine (finish Day 33)

Ranking, sharding, freshness, tenant isolation. Then Day 38 re-tests this
material cold — gate for Phase 3 is ≥ 8/10.
