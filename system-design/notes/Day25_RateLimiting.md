# Day 25: Distributed Rate Limiting Service

**Date:** 2026-08-20  
**Status:** 🔄 In Progress (Core design complete, failure handling + algorithm pending)  
**Confidence:** 7/10 (solid on distribution, needs clarity on algorithms)  
**Communication Level:** 7/10 → Target 8.5/10

---

## System Overview

**What:** Rate limiting service for multi-tenant SaaS (SalesPoint fintech)  
**Scale:** 
- 100K tenants
- 50K req/sec peak (global)
- 16K req/sec midnight
- Multi-region (NZ, AUS)

**SLA:** <5ms response time, strong consistency (no overage allowed)

---

## Bottleneck Identified

### Primary Bottleneck: Redis Hotspot
With 50K req/sec hitting a single regional Redis instance:
- Redis throughput limit: ~100K ops/sec
- Rate limit operations: 2 ops/req (read counter + increment)
- **Result:** 50K × 2 = 100K ops = at capacity ceiling ❌

**Consequence:** Latency spikes, potential rejections of valid requests, cascading failures.

---

## Architecture Design

### 1. Regional Sharding Strategy ✅
```
NZ Region:
  ├── Redis Instance 1-5 (tenant distribution)
  └── Rate limit key scope: NZ tenants only

AUS Region:
  ├── Redis Instance 1-5 (tenant distribution)
  └── Rate limit key scope: AUS tenants only
```

**Why:** Isolate traffic by geography, reduce single point of failure.

---

### 2. Tenant-Based Consistent Hashing ✅
```
Key Distribution:
  hash(tenant_id) % num_instances → determines Redis instance
  
Example (5 instances per region):
  hash(tenant_123) % 5 = 2 → Redis Instance 2
  hash(tenant_456) % 5 = 2 → Redis Instance 2 (same instance)
  hash(tenant_789) % 5 = 1 → Redis Instance 1
```

**Benefit:** Same tenant always routes to same instance (no distributed coordination).  
**Cost:** Traffic skew — if one tenant dominates, that instance becomes hot.

---

### 3. Sub-Sharding for Hot Tenants ✅
```
Normal Tenants (< 1K req/sec):
  hash(tenant_id) % num_instances

Hot Tenants (> 1K req/sec):
  hash(tenant_id + endpoint) % num_instances
  
Spreads mega-customer across multiple instances:
  tenant_mega + POST /invoices → Instance 1
  tenant_mega + GET /reports → Instance 3
  tenant_mega + POST /payments → Instance 2
```

**Trigger:** Monitor instance health metrics (CPU > 70%, latency p99 > 10ms).  
**When detected:** Automatically sub-shard that tenant's endpoints.

---

### 4. Data Consistency: Primary-Only Approach ✅
```
❌ Wrong: Read from replica, write to primary
   (Replica lag causes eventual consistency → overshoots limit)

✅ Right: All reads & writes go to PRIMARY
   (Replicas exist only for failover/HA, not read scaling)
```

**Why:** Rate limiting requires strong consistency.  
- Replica lag (100ms-1s) = requests allowed when they should be rejected
- Example: Limit=1000, Primary=1000, Replica=999 → allows overage

---

### 5. Redis Key Structure ✅
```
Key Format:
  rate_limit:{region}:{service}:{endpoint}:{tenant_id}
  
Example:
  rate_limit:nz:invoicing:POST_/api/invoices:tenant_123
  
Value: Current count (incremented on each request)
TTL: 60 seconds (auto-expire per time window)
```

**Why separate keys from topology?** 
- Key = data identifier (immutable, what you look up)
- Routing = application concern (how you route to Redis instance)

---

### 6. Memory Management ✅
```
Time Windows Stored:
  • 1-minute window: 100K keys × ~56 bytes = 5.6 MB
  • 1-hour window: 100K keys × ~56 bytes = 5.6 MB
  • 1-day window: 100K keys × ~56 bytes = 5.6 MB
  Total: ~16.8 MB (manageable)

Expiration Strategy:
  • Use Redis EXPIRE command: key expires after window closes
  • TTL = 60 seconds for 1-min window
  • TTL = 3600 seconds for 1-hour window
  • Old windows automatically cleaned up (no manual job needed)

Cold Storage:
  • Archive counters to cheaper storage (CosmosDB, S3) for audit/compliance
  • Reduces Redis memory pressure
```

---

## Design Decisions & Tradeoffs

| Decision | Choice | Why | Tradeoff |
|----------|--------|-----|----------|
| **Consistency Model** | Strong (primary-only) | Rate limiting must be accurate; overage = revenue loss | Cannot scale reads to replicas |
| **Tenant Partitioning** | Consistent hashing by tenant_id | Deterministic, no distributed coordination | Hot tenants create uneven load (mitigated by sub-sharding) |
| **Sub-Sharding Trigger** | Instance health metrics (CPU/latency) | Reactive to actual system stress, not arbitrary thresholds | Requires good monitoring; may have slight lag before sub-sharding kicks in |
| **Memory Strategy** | TTL + cold storage | Efficient, no manual cleanup | Query old data requires archive lookups |

---

## Open Questions (Tomorrow)

1. **What happens when Redis is down?**
   - Fallback strategy? (hard reject? soft degradation?)
   - How long can the system tolerate Redis outage?

2. **Which rate limiting algorithm?**
   - Token bucket? (smooth out bursts)
   - Sliding window? (exact accuracy)
   - Fixed window? (simplest, but can have burst at boundary)
   - Why one over the others?

3. **How does the app call the rate limiter?**
   - Inline check before processing?
   - Async check?
   - What does the API surface look like?

---

## Communication Progress

### Yesterday (Day 24): 6.5/10
- Stream-of-consciousness explanations
- Hesitant language ("maybe", "might be")
- Minimal structure

### Today (Day 25): 7/10 ✅ (+0.5 improvement)
**What's Better:**
- ✓ Concrete examples (hash(tenant_id) % 5 = instance)
- ✓ Clear problem → solution flow
- ✓ Threshold clarity (1K req/sec, 10x imbalance)

**Still Needs Work:**
- ⚠️ Some sentence fragments ("Consistent hashing gives a way how to...")
- ⚠️ Could be more polished ("In my design, X because Y")
- ⚠️ Missing brief reasoning sometimes

**Target by end of Day 27:** 8.5/10 (confident, structured, complete reasoning)

---

## Key Learnings

### Bottleneck-First Framework (Reinforced from Day 24)
✓ Different systems break in different ways  
✓ Rate limiting breaks on **coordination** (hotspot in Redis)  
✓ Design questions should target that bottleneck, not generic checklist  

### Distributed Systems Reality
✓ Consistency ≠ always possible (strong consistency can't scale reads)  
✓ Health monitoring > arbitrary thresholds (detect hot instances by metrics, not guess)  
✓ Failure modes are design constraints (Redis down = must have fallback)  

### Data vs. Topology
✓ Keys are data (immutable identifiers)  
✓ Routing is architecture (application concern)  
✓ Don't mix them in key structure  

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Regional sharding** | 9/10 — Clear and justified |
| **Tenant-based hashing** | 8/10 — Good, minor nuance on consistent hashing vs modulo |
| **Sub-sharding strategy** | 7/10 — Right idea, needs clarity on triggers |
| **Primary-only consistency** | 8/10 — Understand why, could articulate better |
| **Memory management** | 8/10 — TTL + cold storage is solid |
| **Failure handling** | 3/10 — ❌ Not yet designed |
| **Algorithm choice** | 2/10 — ❌ Not yet designed |
| **API surface** | 2/10 — ❌ Not yet designed |

**Overall System Confidence: 7/10**

---

## Next Session (Day 25 Completion)

**Topics to design:**
1. Failure handling (Redis down scenarios)
2. Rate limiting algorithm (token bucket vs sliding window vs fixed window)
3. API surface (how app calls the rate limiter)

**Communication focus:**
- Structure answers: Problem → Approach → Why
- Show reasoning, not just conclusions
- Polish language (no hesitation, confident framing)

**Target:** Complete Day 25 design + move to 8/10 communication

---

**Status:** 🔄 In Progress → Ready to resume tomorrow  
**Brain State:** 🧠 Cognitively saturated (good, healthy learning pace)  
**Next:** Rest, optional light review of "what breaks if Redis goes down?"
