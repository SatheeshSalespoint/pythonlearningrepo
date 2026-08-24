# Day 26: Cache Invalidation System

**Date:** 2026-08-21  
**Status:** ✅ Done  
**Confidence:** 8/10 (excellent domain thinking, production-ready design)  
**Communication Level:** 7.5/10 → 8/10 ✅ (target achieved!)

---

## System Overview

**What:** Cache invalidation strategy for multi-tenant fintech SaaS  
**Context:** SalesPoint (accounts, transactions, payment records)  
**Scale:**
- 100K tenants
- 50K req/sec peak
- Multi-region (NZ, AUS)

**Core Problem:** Keep cached data fresh (minimize staleness) while keeping it fast (avoid cache miss storms)

---

## Bottleneck Identified

### Primary Bottleneck: Consistency vs Performance

**The Paradox:**
```
Without cache:
  ✓ Always consistent (fresh data)
  ❌ Slow (50-200ms DB latency)

With cache:
  ✓ Fast (<5ms)
  ❌ Might be stale (outdated data)
```

**For fintech, the bottleneck is CONSISTENCY:**
- Stale balance data → customer makes wrong decisions
- Silent data inconsistency → worse than system down
- Regulatory/compliance risk if customer loses trust

**Other bottlenecks ranked by fintech severity:**
1. **Consistency** (PRIMARY) — Wrong data breaks trust ❌
2. **Performance** — System slow but data intact ⚠️
3. **Staleness** — Recoverable by user refresh ✓
4. **Invalidation complexity** — Design-time problem, not runtime

---

## Staleness Tolerance Framework

Different data types have different consistency requirements:

### Account Balance
```
Tolerance: < 5 seconds
Why: User workflow = transaction → 2-3s navigation → balance screen
     5s is forgiving enough for this flow
     
Consequence if violated: Customer sees old balance, confusion
Recovery: User refreshes → sees correct data
Risk level: Medium (annoying, but recoverable)
```

### Transaction Status
```
Tolerance: < 1 second
Why: Critical decision point — user decides to RETRY or CLOSE transaction
     Decision is IMMEDIATE, can't wait 5 seconds
     
Consequence if violated: User closes transaction that was actually pending
Recovery: None (wrong decision already made)
Risk level: HIGH (affects transaction outcome)
```

### Payment Records (History)
```
Tolerance: < 5 seconds
Why: Historical data, non-time-critical
     User doesn't make immediate decisions based on history
     
Consequence if violated: Outdated transaction history shown
Recovery: Refresh or wait
Risk level: Low (non-critical data)
```

---

## Invalidation Strategy Design

### Transaction Status: Hybrid (Event-Driven + TTL Fallback)

```
NORMAL FLOW:
  1. Transaction completes
  2. Service publishes: "TransactionCompleted" event (with user_id)
  3. Cache listener receives event
  4. Invalidates: cache[user_id][transaction_status]
  5. Next request from user → MISS → fetches fresh from DB → re-caches
  
  Result: Instant invalidation (milliseconds) ✓

FAILURE CASE (Event lost):
  1. Cache TTL expires (1 second timeout)
  2. Next request → MISS → fetches from DB
  3. Re-caches with fresh data
  
  Result: Latest data within 1s, guaranteed ✓

Why Hybrid:
  • Event-driven: Instant updates for critical data
  • TTL fallback: Safety net if event system fails
  • Scoped events: Only invalidate changed user's transaction, not all
```

**Tradeoff:**
```
Pro: ✓ Instant invalidation when event succeeds
     ✓ Reliable fallback if events fail
     ✓ 1s guarantee worst-case
Con: ❌ Slight complexity (pub/sub infrastructure)
     ❌ Event delivery overhead at scale (per transaction)
```

---

### Account Balance: Hybrid (Event on Transaction + TTL)

```
NORMAL FLOW:
  1. Transaction completes
  2. Service publishes: "AccountBalanceUpdated" event (with user_id, new_balance)
  3. Cache listener receives event
  4. Invalidates: cache[user_id][account_balance]
  5. Next request → MISS → fetches fresh → re-caches

FAILURE CASE:
  1. Cache TTL expires (5 second timeout)
  2. Next request → MISS → fetches from DB → re-caches
  
  Result: Latest data within 5s

Why NOT event-driven alone:
  • If we publish account update for EVERY account change, that's 100K events/sec
  • DB would be overloaded with listener traffic
  • Better: Publish only when transaction completes (scoped, not all accounts)

Why Hybrid:
  • Event fires only on transaction completion (controlled)
  • Targets only the user whose balance changed (scoped)
  • TTL fallback covers 5s window if event fails
```

**Tradeoff:**
```
Pro: ✓ Efficient event publishing (only on changes)
     ✓ 5s tolerance is forgiving (acceptable staleness)
     ✓ Scoped invalidation (single user, not broadcast)
Con: ❌ User might see slightly old balance for 5s max
     ❌ More complex than TTL-only
```

---

### Payment Records: TTL-Only

```
SIMPLE FLOW:
  1. Cache key expires after 5 seconds (automated)
  2. Next request → MISS → fetches history from DB → re-caches
  
Why NOT event-driven:
  • Historical data, non-critical
  • Users don't make immediate decisions based on history
  • Event overhead not worth it for non-critical data

Why NOT hybrid:
  • 5s tolerance is long enough for historical data
  • Unnecessary complexity
```

**Tradeoff:**
```
Pro: ✓ Simplest approach
     ✓ No pub/sub infrastructure needed
     ✓ No event overhead
Con: ⚠️ Users see history up to 5s old
     ⚠️ No instant refresh capability
```

---

## Event Infrastructure: Outbox Pattern

### Why Outbox Pattern?

```
PROBLEM with simple pub/sub:
  Event publishing fails → Message lost
  (Transaction written to DB, but event never published)
  → Cache never invalidated → Stale data forever ❌

SOLUTION: Outbox Pattern (Guaranteed Delivery)
  ✓ Atomically write transaction + event to DB
  ✓ Background job publishes events to queue
  ✓ If job fails, it picks up where it left off
  ✓ If queue is down, events stay in outbox until queue recovers
```

### Outbox Pattern Implementation

```
STEP 1: Transaction completes (Atomic)
  BEGIN TRANSACTION
    INSERT into transactions (id, user_id, amount, status)
    INSERT into outbox (transaction_id, event_type, payload, published=false)
  COMMIT
  
  Result: Both written or both rolled back (atomic) ✓

STEP 2: Background job (Worker)
  Every 100ms:
    SELECT * from outbox WHERE published = false LIMIT 100
    FOR each row:
      Publish to message queue (Kafka/RabbitMQ)
      UPDATE outbox SET published = true WHERE id = row.id
    
  Result: Guaranteed delivery (exactly-once semantics) ✓

STEP 3: Failure handling
  • Worker crashes: Resumes, finds unpublished rows, continues
  • Queue down: Data stays in outbox, retries forever
  • Event publish fails: Stays unpublished, retries next cycle
  • App crashes: DB survives, worker continues when app restarts
```

**Tradeoff:**
```
Pro: ✓ Guaranteed delivery (no data loss)
     ✓ Exactly-once semantics (no duplicates)
     ✓ Survives queue outages
     ✓ Survives worker crashes
Con: ⚠️ Slight delay: 100-500ms background job latency
         (acceptable for 1s transaction status tolerance)
     ⚠️ Extra DB table + polling overhead
     ⚠️ Not suitable for real-time (millisecond) requirements
```

---

## Design Decisions & Architecture

| Decision | Choice | Why | Tradeoff |
|----------|--------|-----|----------|
| **Staleness tolerance per data type** | Differentiated (1s/5s/5s) | Fintech: consistency critical for some, not all | Must think per-endpoint, more complex |
| **Transaction status invalidation** | Hybrid (event + TTL) | Instant + reliable | More infrastructure than TTL-only |
| **Account balance invalidation** | Hybrid (event + TTL) | Efficient events + fallback | 5s staleness window acceptable |
| **Payment records invalidation** | TTL-only | Historical data non-critical | Simple, no event overhead |
| **Event delivery guarantee** | Outbox pattern | No data loss | 100-500ms delay (acceptable) |
| **Event scope** | Per-user (not broadcast) | Efficiency at scale | Need message routing by user_id |

---

## Architecture Diagram (Text)

```
WRITE PATH (Transaction Completes):
  Transaction Service
    ↓
  Write to DB (atomic with events)
    ├─ transactions table (data)
    └─ outbox table (events to publish)
    ↓
  Background Worker (polls outbox)
    ↓
  Message Queue (Kafka/RabbitMQ)
    ↓
  Cache Listeners (per region)
    ├─ NZ listener: "TransactionCompleted for user_123" → Invalidate NZ Redis
    └─ AUS listener: "TransactionCompleted for user_456" → Invalidate AUS Redis

READ PATH (User requests balance):
  User request
    ↓
  App checks: Is cache[user_id][balance] fresh?
    ├─ Cache HIT (< 5s old) → Return cached value (1-5ms)
    └─ Cache MISS (expired or invalidated) → Fetch from DB (50-200ms)
                                              → Write to cache (TTL = 5s)
                                              → Return fresh value
```

---

## Key Learnings

### Fintech Thinking
✓ Different data types = different consistency requirements  
✓ Consistency > Availability for financial systems  
✓ Silent data inconsistency > System downtime (worse because it's invisible)  

### Scale-Aware Design
✓ Event-driven invalidation is SCOPED, not broadcast  
✓ 100K events/sec on all changes = system overload  
✓ Publish only on critical changes = sustainable at scale  

### Reliability Patterns
✓ Outbox pattern = guaranteed delivery (exactly-once)  
✓ TTL fallback = safety net for unreliable event systems  
✓ Hybrid approach = best of both worlds (instant + reliable)  

### Production Thinking
✓ Every caching decision has a tradeoff  
✓ Know your staleness tolerance BEFORE designing  
✓ Different data = different strategies (not one-size-fits-all)  

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Bottleneck identification** | 9/10 — Correctly prioritized consistency |
| **Staleness tolerance thinking** | 9/10 — User workflow-based, pragmatic |
| **Scoped event design** | 9/10 — Avoided scale pitfall, smart optimization |
| **Outbox pattern** | 10/10 — Experience-backed, explained well |
| **Tradeoff analysis** | 8/10 — Good, could be more explicit |

**Overall Day 26:** 8/10 ✅

---

## Communication Progress

### Day 24 → Day 26 Journey

| Metric | Day 24 | Day 25 | Day 26 |
|--------|--------|--------|--------|
| **Communication** | 6.5/10 | 7.5/10 | 8/10 ✅ |
| **Structure** | Fragmented | Improved | Excellent |
| **Confidence language** | Hesitant | Better | Strong |
| **Self-correction** | Rare | Emerging | Excellent |

### What Improved in Day 26
- ✓ **Self-correction:** "Let me refine my answer" (caught over-broad events)
- ✓ **Tradeoff thinking:** Compared options, explained why chosen
- ✓ **Scoped reasoning:** Not just "use events," but "scoped events per user"
- ✓ **Experience-backed:** "I have done this approach before" (confidence)
- ✓ **Domain thinking:** Differentiated by fintech needs

### Still Room to Polish (Day 27)
- ⚠️ When explaining tradeoffs, explicitly state "Pro: X, Con: Y"
- ⚠️ Sometimes could be more concise (trim explanations)
- Target for Day 27: **8.5/10** (polish, brevity, pro/con clarity)

---

## Next Session: Day 27 — Metrics & Monitoring System

**What breaks with metrics at scale?**
- Cardinality explosion (100K metrics × 10 tags = 1M time series)
- Aggregation bottleneck (summing 1M time series in real-time)
- Storage explosion (time-series DB growth)
- Query latency (finding specific metric among millions)

**Communication target:** 8/10 → 8.5/10 (final polish)

---

**Status:** ✅ Complete — Ready for Day 27  
**Brain State:** 🧠 Good energy remaining, ready for final polish day  
**Next:** Day 27 wraps communication to 8.5/10, completes Phase 1
