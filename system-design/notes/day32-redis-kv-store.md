# Day 32: Redis-Style Key-Value Store (Persistence, Eviction, Pub/Sub)

**Date:** 2026-09-02  
**Duration:** ~40 mins  
**Status:** ✅ Complete (Design & Architecture Decisions)  
**Difficulty:** Medium  
**Confidence Level:** 8.5/10 (Strong architectural decisions for SalesPoint)  
**Communication Level:** 8.5/10 (Excellent bottleneck identification & reasoning)

---

## The Challenge

Design a **Redis-style in-memory key-value store** that balances three competing concerns: **persistent storage** (don't lose critical data), **memory management** (eviction when full), and **event delivery** (pub/sub for notifications).

**Real-World Context (SalesPoint Fintech):**
```
Redis stores:
  1. User sessions (CRITICAL - can't lose)
  2. Rate limit values (CRITICAL - must be accurate)
  3. Idempotency keys (CRITICAL - prevent duplicate transactions)
  4. Settings/config (non-critical - refetch from DB)
  5. Cached queries (non-critical - regenerate from DB)
  6. Frequently accessed data (non-critical - evict safely)
```

**Key Requirements:**
- **Durability:** Sessions must survive Redis crash (multi-instance auth architecture)
- **Memory efficiency:** LRU/LFU eviction when store is full
- **Fast recovery:** 5 seconds acceptable downtime
- **No data loss:** Critical data (sessions, rate limits) must persist
- **Scalability:** Support 100K concurrent sessions, 50K req/sec

---

## Bottleneck Analysis: Three Critical Concerns

### Bottleneck 1: Session Persistence (PRIMARY ⚠️⚠️⚠️)

**Problem:**
```
Single shared Redis instance for all auth service instances
  • If Redis crashes → ALL users logged out
  • No shared sessions across auth servers
  • Recovery must be fast (<5 seconds)
```

**Why It's Critical:**
- Multi-instance auth architecture (Server-1, Server-2, Server-3 share ONE Redis)
- User logout = poor UX, loss of trust
- Fintech: Session data loss breaks customer workflows

**Solution: RDB + AOF Persistence**

```
RDB (Snapshot-Based):
  • Take full snapshot every 5 minutes
  • Save to disk (fast, compact recovery)
  • Problem: Loses data between snapshots

AOF (Append-Only File):
  • Log EVERY write operation to disk
  • Example: SET session:user123 "token_xyz"
  • Problem: Slower recovery (must replay all ops)

HYBRID (RDB + AOF):
  • Load RDB snapshot (fast recovery in 1 second)
  • Replay AOF since last RDB (catch missed sessions)
  • Result: FAST recovery + ZERO data loss
```

**Timeline Example:**
```
4:00 PM → RDB snapshot (sessions 0-300s)
4:00-4:03 → AOF logs new sessions (A, B, C)
4:03 PM → Redis crashes
4:03 PM → Restart: Load RDB (1s) + replay AOF (2s) = 3s recovery
Result: ALL sessions recovered ✓
```

**Tiered Sync Strategy (to DB):**
```
Critical data (sessions, rate limits, idempotency keys):
  → Sync to DB every 1 minute (minimize loss window)

Non-critical data (queries, settings):
  → Sync to DB every 5 minutes (acceptable loss)
```

### Bottleneck 2: Memory Eviction (SECONDARY)

**Problem:**
```
Redis max_memory = 10GB
Current usage = 9.5GB
New query cache (500MB) requested
Memory FULL, no TTL expired yet
→ What gets deleted?
```

**Data Types & Eviction Strategy:**

| Data Type | Evictible? | Policy | Reasoning |
|-----------|-----------|--------|-----------|
| Sessions | NO (Protected) | Never evict, expire by TTL only | User logout = critical failure |
| Rate limits | NO (Protected) | Never evict, expire by TTL only | Accuracy critical for fintech |
| Idempotency keys | NO (Protected) | Never evict, expire by TTL only | Duplicate transactions catastrophic |
| Settings | YES (Can evict) | Fetch fresh from DB | Non-critical, refetchable |
| Cached queries | YES (Can evict) | LFU eviction | Regenerate from DB if needed |
| Frequently accessed data | YES (Can evict) | LFU eviction | Common data stays, rare goes |

**Eviction Policy Decision: LFU (Least Frequently Used)**

```
LFU vs LRU Comparison:

LRU (Least Recently Used):
  Delete: Data not accessed in longest time
  Good for: Temporal locality ("recent = hot")
  Example: Query not used in 1 hour → delete

LFU (Least Frequently Used):
  Delete: Data accessed least often
  Good for: Popularity patterns ("heavy hitters stay")
  Example: Query A used 5 times/day, Query B used 100 times/day → delete A

Choice: LFU for SalesPoint
  • Popular queries (customer lookups, balance checks) stay in cache
  • Rare queries (edge cases, reports) get evicted first
  • Better performance for 80/20 workload
```

**Implementation Details:**
```
class RedisStore:
    def __init__(self, max_memory=10GB):
        self.data = {}                    # key → (value, metadata)
        self.access_count = {}            # key → frequency
        self.max_memory = max_memory
        self.critical_keys = set()        # Protected from eviction
    
    def get(self, key):
        if key in self.data:
            self.access_count[key] += 1  # Track frequency
            return self.data[key][0]
        return None
    
    def set(self, key, value, is_critical=False):
        # Evict LFU if memory full
        while self._total_size() + size > self.max_memory:
            # Only evict non-critical data
            lfu_key = self._find_least_frequent_non_critical()
            del self.data[lfu_key]
        
        self.data[key] = (value, metadata)
        if is_critical:
            self.critical_keys.add(key)
        self.access_count[key] = 1
```

### Bottleneck 3: Pub/Sub (NOT A BOTTLENECK ✓)

**Analysis:**
```
Your use case for pub/sub:
  • Payment notifications → RabbitMQ (not Redis pub/sub)
  • Transaction alerts → RabbitMQ (not Redis pub/sub)
  • Password reset → RabbitMQ (not Redis pub/sub)

You ALREADY have:
  • RabbitMQ + Notification Service (Day 30-31)
  • Guaranteed delivery ✓
  • Multi-channel support ✓
  • Retry logic ✓

Result: Redis pub/sub is NOT needed
  → Use RabbitMQ for all notifications
  → Redis only for storage/caching
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│       In-Memory Hash Table (Redis)          │
│  • Sessions, rate limits, cache, settings   │
├─────────────────────────────────────────────┤
│    Persistence Layer (RDB + AOF)            │
│  • RDB: Snapshot every 5 mins               │
│  • AOF: Log every write operation           │
│  • Recovery: Load RDB + replay AOF          │
├─────────────────────────────────────────────┤
│    Memory Manager (LFU Eviction)            │
│  • Protect critical data (sessions, etc)    │
│  • Evict least-frequent non-critical data   │
│  • Cache stampede prevention (TTL)          │
├─────────────────────────────────────────────┤
│    Background Workers (DB Sync)             │
│  • Critical: Sync 1-min to DB               │
│  • Non-critical: Sync 5-min to DB           │
│  • Failure recovery: Rebuild from DB        │
└─────────────────────────────────────────────┘
```

---

## Key Decisions & Tradeoffs

### Decision 1: RDB + AOF Persistence

**Tradeoff Analysis:**

| Approach | Recovery Speed | Data Loss | Complexity | Choice |
|----------|----------------|-----------|-----------|--------|
| RDB only | ⚡ Fast (1s) | 5 min data loss | Low | ❌ Risky |
| AOF only | 🐢 Slow (minutes) | ~0 loss | Medium | ❌ Too slow |
| RDB + AOF | ⚡ Fast (3-5s) | ~0 loss | High | ✅ Best |

**Why RDB + AOF:**
- Fast recovery (RDB loads snapshot in 1 second)
- Zero data loss (AOF catches what RDB missed)
- Acceptable complexity for fintech
- 5-second recovery meets requirement

**Alternative fallback:** If RDB + AOF proves too complex, use RDB-only with 1-minute snapshots

### Decision 2: LFU Eviction with Critical Data Protection

**Tradeoff Analysis:**

| Policy | Heavy Hitters | Recent Data | Complexity | Choice |
|--------|---------------|-------------|-----------|--------|
| LRU | May evict popular | Keeps recent | Low | ❌ Sub-optimal |
| LFU | Keeps popular | May evict recent | Medium | ✅ Best for SalesPoint |
| Random | Unpredictable | Unpredictable | Low | ❌ Poor UX |

**Why LFU:**
- Preserves popular queries (80/20 workload typical)
- Better cache hit ratio for fintech
- Medium complexity acceptable

**Critical data protection:**
- Sessions, rate limits, idempotency keys: NEVER evict
- Only expire by TTL
- Filter at eviction policy level

### Decision 3: Tiered Sync (DB Sync Strategy)

**Reasoning:**
```
RDB + AOF handle in-memory persistence
DB sync handles disaster recovery (Redis completely lost)

Critical data (1-min sync):
  → Sessions: User logout if lost
  → Rate limits: Accuracy critical
  → Idempotency keys: Duplicate transactions catastrophic

Non-critical data (5-min sync):
  → Queries: Refetch from DB
  → Settings: Refetch from DB
  → Frequently accessed: Refetch with slight delay
```

---

## Interview Approach (Bottleneck-First Method)

**When asked: "Design a Redis-style KV store"**

**Step 1: Ask Clarifying Questions**
```
YOU: "A few questions to understand constraints:

1. What's the primary use case? (Caching, sessions, rate limiting?)
2. What data CANNOT be lost if it crashes? (This identifies persistence need)
3. What's the scale? (Requests/sec, data size, regions?)
4. Recovery time tolerance? (5 seconds? 5 minutes?)"
```

**Step 2: Interviewer Answers**
```
Typical answer:
"Sessions + caching, sessions matter, 100K req/sec, 5 sec recovery"
```

**Step 3: Identify & Confirm Bottleneck**
```
YOU: "So the PRIMARY bottleneck is session persistence 
(can't lose sessions on crash). 
SECONDARY is memory eviction (100GB needs management). 
Is that right?"
```

**Step 4: Design to Solve Bottleneck**
```
YOU: "For persistence: RDB + AOF
      - RDB snapshots fast (1s recovery)
      - AOF logs writes (catch missed sessions)
      - Together: Fast + durable
      
     For eviction: LFU with critical data protection
      - LFU keeps popular queries (80/20 pattern)
      - Protect sessions (never evict)
      - Expire by TTL only"
```

**Step 5: Discuss Tradeoffs**
```
INTERVIEWER: "What if RDB snapshots are too slow?"

YOU: "Good question. Tradeoff:
     - RDB is fast recovery but loses data between snapshots
     - AOF is durable but slow to recover
     - RDB + AOF is best but more complex
     
     For fintech, I'd choose RDB + AOF because 
     data loss > complexity. But if disk I/O becomes bottleneck,
     I'd fall back to RDB-only with 1-min snapshots."
```

---

## Implementation Considerations

### What to Code

**Phase 1 (12 min): Core Store**
- Hash table with `get/set/delete`
- TTL tracking (expiry on access)
- Thread-safe with locks

**Phase 2 (10 min): LFU Eviction**
- Track frequency per key
- Find least-frequent on memory breach
- Protect critical keys (sessions, rate limits)

**Phase 3 (12 min): Persistence**
- RDB: Serialize store every 5 mins
- AOF: Log every SET/DEL operation
- Recovery: Load RDB + replay AOF

**Phase 4 (6 min): Testing**
- Crash simulation (kill Redis, verify recovery)
- Eviction verification (fill beyond max_memory, check LFU removed)
- TTL expiry (check critical data expires correctly)

### Critical Design Patterns

```python
# Critical data protection
set("session:user123", token, critical=True, ttl=1_hour)
set("rate_limit:endpoint:tenant", count, critical=True, ttl=1_minute)

# Non-critical (can evict)
set("query_result:abc", data, critical=False, ttl=5_minutes)

# Eviction never touches critical_keys
def evict_lfu():
    for key in sorted_by_frequency():
        if key not in critical_keys:  # Skip protected
            delete(key)
            break
```

---

## Checkpoint: Day 32 Assessment

**Self-Assessment Questions:**
- ✓ Can you explain RDB vs AOF tradeoff? (With timeline example)
- ✓ Why LFU for SalesPoint? (80/20 workload, heavy hitters matter)
- ✓ How do you protect critical data? (Filter at eviction policy)
- ✓ When would you use RDB-only fallback? (If RDB + AOF too complex)
- ✓ How does this connect to your notification system? (RabbitMQ handles pub/sub, not Redis)

**Confidence Check:**
- Technical: 8.5/10 (Strong decisions, clear reasoning)
- Communication: 8.5/10 (Excellent bottleneck identification)
- Readiness for Day 33: ✅ Yes (Phase 3 hard systems ready)

---

## Next Session: Day 33

**Topic Options:**
- Distributed Transaction System (2-phase commit, consensus)
- Global CDN & Edge Caching (geo-replication, consistency)
- Real-time Collaborative Editor (OT or CRDT algorithms)

**Current Status:** Days 1-32 complete. Checkpoint at Day 35. On track for Phase 3 (Hard systems).

