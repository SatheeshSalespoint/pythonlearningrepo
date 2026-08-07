# Day 17: Consistent Hashing

**Date:** 2026-08-07  
**Duration:** ~30 mins (with Q&A)  
**Status:** ✅ Complete

---

## Core Concept

**Problem:** Simple hashing breaks at scale. When you add a node, `hash(key) % num_nodes` causes ALL keys to rehash → thundering herd at DB.

**Solution:** Place nodes and keys on a circular ring. A key lives on the **next node clockwise**. When you add a node, **only affected keys rehash** (~1/N of all keys, not all).

---

## The Ring (Linear Representation)

```
0° ——— 100° ——— 400° ——— 600° ——— 800° ——— 360°
   |           |           |           |
 Node A      Node B      Node D      Node C
```

**Rule:** Start at key's position, go RIGHT (clockwise) until hitting the first node.

**Example:** Key at 350° → 350° → 400° → [HIT Node B]

---

## When Does a Key Rehash?

**A key only rehashes if a new node is inserted BETWEEN the key's position and its current owner (clockwise).**

**Example:**
- Key at 750°, currently owned by Node C (800°)
- Add Node D at 850°? → 850° is NOT between 750° and 800° → NO rehash ✅
- Add Node D at 760°? → 760° IS between 750° and 800° → YES rehash ✅

---

## Real-World Applications

| System | What's Hashing | Example |
|--------|---|---|
| **Redis Cluster** | Cache key | Which node stores `session:user123`? |
| **Kafka** | Message key | Which partition gets `order_id:456`? |
| **Database Sharding** | Entity ID | Which shard holds `user_789`'s data? |
| **Load Balancing** | Session ID | Which app server handles `session_xyz`? |
| **Rate Limiting** | Tenant ID | Which rate limit node tracks `tenant_456`? |

---

## Key Design Decisions

### 1. Simple Hashing vs Consistent Hashing
- **Simple:** 10 → 15 nodes = **~67% keys rehash** ❌
- **Consistent:** 10 → 15 nodes = **~33% keys rehash** ✅

### 2. Kafka: Key Choice Matters
- **Key = order_id:** Orders spread evenly, BUT no ordering per customer ❌
- **Key = customer_id:** All customer orders ordered, BUT hot partition if customer is huge ✅
  - **Tradeoff:** Correctness > Load balancing

### 3. Hot Spot Problem (Mega-corp Tenant)
- **Without fix:** Mega-corp dominates every node (90% of cache on each node)
- **With sub-partitioning:** Add `shardId` to key → spread mega-corp across nodes

---

## The Gotcha: Consistent Hashing Doesn't Solve Everything

> **Consistent hashing distributes KEYS evenly, but not DATA FAIRLY across TENANTS.**

**Fix: Sub-partition keys**
```csharp
// Before (unbalanced)
key = $"tenant:megacorp:data:{dataId}"

// After (balanced)
key = $"tenant:megacorp:shard:{shardId}:data:{dataId}"
// shardId = Hash(dataId) % 10
```

This spreads mega-corp's data more evenly, reducing thundering herd risk.

---

## Key Takeaway

> **Consistent hashing lets you scale systems without massive cache misses. Use it wherever you partition: Redis, Kafka, databases. But remember: it solves "when keys rehash," not "how to balance skewed data."**

---

## Questions Learned Today

1. ✅ Ring mechanics & clockwise traversal
2. ✅ Why keys only rehash when new node lands between key & current owner
3. ✅ Tradeoff in Kafka: ordering (customer_id key) vs load balancing (order_id key)
4. ✅ Rehashing math: Simple (67%) vs Consistent (33%)
5. ✅ Hot spot problem: Mega-corp tenant on every node → fix with sub-partitioning

---

## Next Session (Day 18)

**Topic:** Database Sharding  
**Preview:** How to use consistent hashing to shard databases. Shard key selection. Range-based vs hash-based sharding.
