# Day 18: Database Sharding

**Date:** 2026-08-10  
**Duration:** ~45 mins (with Q&A)  
**Status:** ✅ Complete

---

## Core Concept

**Sharding** = splitting your data across multiple database servers based on a **shard key**. Each shard holds a subset of data. Queries route to the correct shard using the shard key.

**Why:** Single database can't handle 100M+ users. Need horizontal scaling (more servers), not just vertical (bigger server).

---

## The Problem: Single DB Bottleneck

```
1M users   → DB slow
50M users  → DB overloaded
100M users → DB crashes 💥

Solution: Split data across shards
```

---

## Shard Key Selection (Critical Decision)

Your shard key determines how data splits. A bad choice creates **hot shards** (one shard gets 90% of traffic while others sit idle).

### Checklist for Good Shard Key

✅ **High cardinality** (millions of unique values)  
✅ **Immutable** (never changes)  
✅ **Evenly distributed** (avoids skew)  
✅ **Query-aligned** (most queries filter by this)  

❌ **Bad:** Gender, Status, Is-Active (low cardinality = hot shards)

### Shard Key Options

| Shard Key | Best For | Problem |
|-----------|----------|---------|
| `user_id` | User-centric queries (my orders, my profile) | Joins slow (users on different shards) |
| `region` (US/EU/APAC) | Geographic isolation, compliance | Uneven load if regions differ in size |
| `tenant_id` | Multi-tenant SaaS (data isolation) | Hot shards if mega-corp tenant is huge |

**Hybrid Solution:** Primary shard by one key (user_id), secondary index by another (region). Use denormalization/caching for secondary queries.

---

## The Tradeoffs

### Tradeoff 1: Joins Become Slow

**Problem:** Orders sharded by order_id, customers sharded by customer_id → data split across shards.

```sql
-- This query needs to fan out to ALL shards, then join in app
SELECT o.order_id, c.customer_name
FROM orders o
JOIN customers c ON o.customer_id = c.id
```

**Solution:** Keep related data together (orders + customer in same shard by user_id). Or denormalize (store customer name in orders table).

---

### Tradeoff 2: Distributed Transactions Are Risky

**Problem:** Transfer $100 from user_A (Shard 1) to user_B (Shard 2).

**Options:**
- **Async:** Debit Shard 1, send message, credit Shard 2 → if message queue fails, money lost ❌
- **2-Phase Commit:** Coordinate atomically across shards → SLOW, use only if rare
- **Design to avoid:** Keep related entities in same shard (all user data in one shard)

**Best:** Design so cross-shard writes are rare or nonexistent.

---

### Tradeoff 3: Hot Shards from Skewed Data

**Mega-corp shard:** 90% of traffic, 90% of data.

**Solutions:**
- **Sub-sharding:** Split mega-corp by region or user_id sub-range
- **Caching + Read Replicas:** Cache absorbs 90% of reads, replicas handle rest
- **Denormalization:** Keep separate analytics database for aggregations

---

## Two Types of Skew

### Data Skew (Storage Imbalance)

Uneven distribution of **data volume** across shards.

```
Shard A: 100GB (mega-corp)
Shard B: 10GB (small co)
Shard C: 10GB (small co)
→ Shard A disk fills 90% faster
```

**Fix:** Sub-sharding, rebalancing, accept the difference.

### Traffic Skew (Query Load Imbalance)

Uneven distribution of **queries** across shards.

```
Shard A: 50M queries/day (mega-corp)
Shard B: 100k queries/day (small co)
Shard C: 100k queries/day (small co)
→ Shard A CPU maxed, Shard B/C idle
```

**Fix:** Caching (Redis), read replicas, denormalization.

**Key:** Data skew and traffic skew are separate problems. You can have one without the other.

---

## Adding New Shards Safely

When adding Shard 5 to a 4-shard cluster:

**With simple hashing:** ~80% of keys rehash → thundering herd 💥  
**With consistent hashing:** ~33% of keys rehash → manageable

**Production strategy:**
1. **Gradual rollout:** Route 10% → 50% → 100% of new traffic to new shard
2. **Cache lock pattern:** Prevent cache stampede for individual keys
3. **Monitor:** Watch DB, cache hit rate, CPU before full rollout

---

## Real-World Solutions

### For User-Centric Queries

```
Shard by: user_id
Result: "Get my orders" hits ONE shard → FAST ✓
Problem: "Get trending products" hits ALL shards → SLOW ✗
Solution: Separate analytics database (denormalized, updated async)
```

### For SaaS Multi-Tenant

```
Shard by: tenant_id
For mega-corp: Caching (Redis) + Read Replicas
Result: Keeps tenant data together (compliance ✓), handles traffic (cache ✓)
```

### For Geographic Data

```
Shard by: region (US, EU, APAC)
Result: Data locality (fast), compliance (EU data stays in EU)
Problem: Uneven load if one region dominates
Solution: Accept it, or sub-shard within region
```

---

## Key Takeaway

> **Sharding scales your database horizontally, but forces hard tradeoffs: joins become slow, distributed transactions are risky, and bad shard key choices create hot shards. Use consistent hashing for rebalancing. Keep related data together. Accept eventual consistency for cross-shard writes. Monitor both data skew and traffic skew separately—they require different fixes.**

---

## Questions Learned Today

1. ✅ Shard key selection (cardinality, immutability, evenness)
2. ✅ Hybrid sharding (primary + secondary index for secondary queries)
3. ✅ Cross-shard join problem → denormalization/analytics database solution
4. ✅ Hot shard mitigation (caching + read replicas)
5. ✅ Data skew vs traffic skew (different problems, different fixes)

---

## Next Session (Day 19)

**Topic:** Replication — Leader/Follower  
**Preview:** How to replicate data across shards/nodes for redundancy and read scaling. Leader-follower pattern, replication lag, consistency guarantees.
