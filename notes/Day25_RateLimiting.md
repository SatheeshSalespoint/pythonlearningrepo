# Day 25: Distributed Rate Limiting Service

**Date:** 2026-08-20  
**Status:** 🔄 In Progress → ✅ Done  
**Confidence:** 7/10 (solid on distribution, failure handling complete)  
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
  • Old windows automatically cleaned up (no manual job needed)

Cold Storage:
  • Archive counters to cheaper storage for audit/compliance
  • Reduces Redis memory pressure
```

---

## Failure Handling Strategy ✅

### When Redis is Down: Hard Reject for Payments

**Decision:** For critical payment endpoints, use HARD REJECT (not soft degrade)

**Why:** 
- Fintech requires consistency, not availability
- Soft degrade → customers exceed quota → revenue loss
- Hard reject → safe, predictable

**Implementation:**
```
1. Deploy hot standby replicas (always running)
2. Monitor primary Redis (health checks every 100ms)
3. Detect failure quickly (3-4 failed attempts)
4. Circuit breaker: STOP TRYING to reach Redis
5. Fall back to: HARD REJECT all payment endpoints
6. Non-critical endpoints: Soft degrade to replica with eventual consistency
7. When primary recovers: Resume normal operation
```

**Result:**
- 99.9% of time: Primary Redis up, fast + accurate ✓
- During rare outage: Payments safe (rejected), non-critical endpoints degrade gracefully

---

## Rate Limiting Algorithm: Token Bucket ✅

**Choice:** Token Bucket (not sliding window)

**Why:**
- **Cheap:** Store only token count + refill rate (not timestamps)
- **Memory efficient:** 2 values vs 100+ timestamps per counter
- **Less accurate:** Might overshoot by a few requests, but temporary
- **Still acceptable:** For non-payment endpoints, this tradeoff is worth it

**How it works:**
```
Tokens = 100 per minute
Refill rate = 1.67 tokens/second

Request arrives:
  1. Check tokens available: 87
  2. Is 87 > 1? Yes → ALLOW
  3. Decrement: tokens = 86
  4. Next second: tokens += 1.67 (refill)

Result: Smooth, predictable, cheap ✓
```

---

## API Surface ✅

**Rate Limiter Call Pattern:**

```
MIDDLEWARE (early rejection):
  Request arrives
    ↓
  Middleware checks: RateLimiter.CheckAndIncrement(tenant_id, endpoint)
    • Read token count from Redis: 87
    • Is 87 > 1? Yes → ALLOW
    • Decrement: tokens = 86
    • Return ALLOW
    ↓
  Request routes to handler (only if rate limit allows)
    ↓
  Process request → Return response
```

**Why middleware:**
- ✓ Consistent for all endpoints
- ✓ Rejects early (before handler runs)
- ✓ Prevents wasting compute on over-limit requests

---

## Design Decisions & Tradeoffs

| Decision | Choice | Why | Tradeoff |
|----------|--------|-----|----------|
| **Consistency Model** | Strong (primary-only) | Rate limiting must be accurate; overage = revenue loss | Cannot scale reads to replicas |
| **Tenant Partitioning** | Consistent hashing | Deterministic, no distributed coordination | Hot tenants create uneven load (mitigated by sub-sharding) |
| **Sub-Sharding Trigger** | Instance health metrics (CPU/latency) | Reactive to actual system stress | Requires good monitoring |
| **Algorithm** | Token bucket | Cheap, efficient at scale | Slight overage possible (acceptable) |
| **Failure Mode** | Hard reject for payments | Safe, no revenue loss | Service appears down (acceptable fintech tradeoff) |

---

## Key Learnings

### Bottleneck-First Framework
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
| **Sub-sharding strategy** | 7/10 — Right idea, triggers on instance health |
| **Primary-only consistency** | 8/10 — Understand why, articulate well |
| **Memory management** | 8/10 — TTL + cold storage is solid |
| **Failure handling** | 8/10 — Hard reject strategy is correct |
| **Algorithm choice** | 8/10 — Token bucket reasoning solid |
| **API surface** | 8/10 — Middleware pattern correct |

**Overall System Confidence: 8/10** ✅

---

## Communication Progress

| Aspect | Day 24 | Day 25 |
|--------|--------|--------|
| **Confidence Level** | 6.5/10 | 7/10 |
| **Structure** | Fragmented | Improving |
| **Language** | Hesitant | More confident |
| **Examples** | Vague | Concrete |
| **Improvement** | — | +0.5 |

**What improved:**
- ✓ Concrete examples (hash(tenant_id) % 5 = instance)
- ✓ Clear problem → solution flow
- ✓ Threshold clarity (1K req/sec, 10x imbalance)

**Still improving:**
- ⚠️ Some fragments
- ⚠️ Could be more polished
- Target: 8.5/10 by end of Day 27

---

**Status:** ✅ Complete — Ready for Day 26  
**Next:** Cache Invalidation (consistency vs performance bottleneck)
