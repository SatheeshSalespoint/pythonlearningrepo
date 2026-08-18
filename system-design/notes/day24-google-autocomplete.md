# Day 24: Case Study — Google Search Autocomplete

**Date:** 2026-08-19  
**Duration:** ~50 mins  
**Status:** ✅ Complete  
**Difficulty:** Medium  
**Confidence Level:** 9-10/10 ⭐⭐⭐

---

## The Challenge

Design an **autocomplete/suggestion system** that appears when users type in a search box.

**User Experience:**
```
User types: "system des"
System returns (instantly, <100ms):
  1. "system design"
  2. "system design interview"
  3. "system design principles"
  4. "system design tutorial"
```

**Requirements:**
- Return suggestions **instantly** (<100ms)
- Show **popular** queries first (ranked)
- Handle millions of concurrent users
- Update rankings as new searches happen
- Handle both popular AND obscure queries

---

## Scale Estimation

### Daily Search Volume

```
Global daily searches: 5B searches/day
Average characters per search: 3 chars
Total characters typed: 5B × 3 = 15B chars

Autocomplete requests per day:
  When user enters 1 char → 1 API call
  When user enters 2 chars → 2 API calls
  When user enters 3 chars → 3 API calls
  
  Total: 15B requests/day

Requests per second:
  Average: 15B ÷ 86,400 sec = 173,611 req/sec
  Peak (3x): 173,611 × 3 = 520,833 req/sec
  Off-peak (1/3): 173,611 ÷ 3 = 57,870 req/sec

Conclusion: EXTREMELY read-heavy system (higher than URL shortener!)
```

---

## Core Data Structure: TRIE (Prefix Tree)

### Why Trie?

Traditional approach (❌ Too slow):
```
SELECT * FROM queries WHERE query LIKE "sys%"
→ Scan billions of rows
→ Time: O(n) where n = 1B queries = SLOW
```

Trie approach (✅ Perfect for prefix matching):
```
Follow pointers: s → y → s
→ All queries starting with "sys" are in this subtree
→ Time: O(m) where m = length of prefix (3-5 chars) = INSTANT
```

### Visual Structure

```
Trie Node Example:

            ROOT
             |
             s
             |
             y
             |
             s
             |
             t
             |
             e
             |
             m
          [MARKER] ✓ "system" is a query
             |
          (space)
           / | \
          d  s  c
          |  |  |
          e  o  a
          |  f  l
          s  t  l
          i  w
          g  a
          n  r
          |  e
       [MARKER] ✓ "system design"
          |
       (space) i n t e r v i e w
          |
       [MARKER] ✓ "system design interview"
```

### Node Structure

```
Each Trie Node stores:

NODE {
  character: 's'
  children: {map of child nodes}
  is_query: true/false
  
  long_term_score: 10,000,000  (all-time popularity)
  short_term_score: 50,000      (last 24 hours)
  combined_rank: 8,050,000      (calculated daily)
  
  top_10_suggestions: [
    "system design interview",
    "system design patterns",
    ...
  ]  (pre-ranked for faster serving)
}
```

---

## Ranking Formula: Balanced Approach

### Decision: Mix of Long-term + Short-term

```
Score = (long_term_popularity × 1.0) + (short_term_trend × 1.0)

Why balanced (equal weights)?
  • For SalesPoint fintech platform
  • Long-term: business metrics, payment flows stay stable
  • Short-term: new features, regulations, security updates
  • Both equally important

Example Calculation:

Query: "system design"
  Long-term: 10,000,000 (all-time searches)
  Short-term: 50,000 (last 24 hours)
  Score: (10M × 1.0) + (50K × 1.0) = 10,050,000

Query: "payment 3D secure"
  Long-term: 500,000 (newly introduced feature)
  Short-term: 100,000 (trending today due to compliance requirement)
  Score: (500K × 1.0) + (100K × 1.0) = 600,000

Result: "system design" ranks higher (established popularity)
        but "payment 3D secure" ranks high (trending)
```

### Weight Tuning (NOT Universal)

```
Different systems use different weights:

Google Search (News Heavy):
  Score = long_term × 0.3 + short_term × 2.0
  (Prioritize trending news)

Wikipedia Search (Quality Heavy):
  Score = long_term × 5.0 + short_term × 0.5
  (Prioritize authoritative content)

Twitter Search (Recency Obsessed):
  Score = long_term × 0.1 + short_term × 10.0
  (Prioritize what's happening RIGHT NOW)

SalesPoint (Balanced):
  Score = long_term × 1.0 + short_term × 1.0
  (Both stability AND new features matter)

KEY INSIGHT: Weights are DESIGN DECISIONS, not universal formulas!
```

---

## Hybrid Storage Architecture

### The Three-Tier System

```
TIER 1: TRIE (Hot - In Memory)
  • Top 1M most popular queries
  • Split: 900K stable + 100K trending
  • Storage: ~1GB
  • Response time: <1ms
  • Use case: Popular queries (99.9% of searches)

TIER 2: REDIS (Warm - Recently Popular)
  • Recently clicked obscure queries
  • Short-term trending that's not in Trie yet
  • Storage: ~500MB
  • Response time: <5ms
  • Use case: Trending obscure queries
  • TTL: 24 hours

TIER 3: DATABASE (Cold - Everything)
  • All 1B unique queries ever searched
  • Ranked but slower to query
  • Storage: ~100GB
  • Response time: 50-200ms
  • Use case: One-off obscure searches
  • Fallback when not in Tier 1 or 2
```

### Why Hybrid Works (Pareto Principle)

```
Real Data Distribution:

Top 1M queries = 99.9% of all searches
  • "system design" = 10M searches/day
  • "payment" = 5M searches/day
  • "login" = 3M searches/day

Remaining 1B queries = 0.1% of searches
  • "xyz obscure term" = 1 search/day
  • "typo from user" = 1 search/day
  • Random nonsense = never again

CONCLUSION: 80% of traffic comes from 20% of queries!
You need top 1M in memory, not all 1B!
```

---

## Complete Query Flow

### User Types "system des"

```
STEP 1: Check Trie (in-memory)
  • Follow pointer path: s → y → s → t → e → m → (space) → d → e → s
  • Time: 10 pointer follows = <1ms
  • Found: All queries starting with "system des"
  
STEP 2: Return pre-ranked results
  • Trie node has top_10_suggestions already calculated
  • Return immediately: <1ms ✓
  • No database query needed!

Response to user:
  1. "system design" (score: 10M + 50K)
  2. "system design interview" (score: 5M + 100K)
  3. "system design patterns" (score: 3M + 20K)
  4. ...
```

### User Types "xyz obscure" (Not in Trie)

```
STEP 1: Check Trie
  • Not found (it's obscure)
  
STEP 2: Check Redis cache
  • Not found (first search)
  
STEP 3: Query Database
  • SELECT * FROM queries 
    WHERE query LIKE 'xyz obscure%' 
    LIMIT 10
  • Time: 50-200ms (acceptable, rare)
  
STEP 4: User clicks "xyz obscure accounting"
  • Increment short_term_count in Redis
  • Cache for next search: <5ms next time ✓
  
STEP 5: Every 30 mins
  • Sync Redis counts to Database
  • Update short_term_count
  
STEP 6: Daily batch job (11:59 PM)
  • Recalculate all rankings
  • If "xyz obscure accounting" ranking > MEDIAN:
    → Promote to Trie ✓
  • Else: Keep in Redis, try again tomorrow
```

---

## Daily Update Strategy

### How Rankings Update (Daily Batch Job)

```
Algorithm (runs at 11:59 PM):

1. Recalculate rankings for ALL queries
   SELECT query, long_term_count, short_term_count
   FROM queries
   ORDER BY combined_rank DESC

2. Calculate threshold (MEDIAN ranking)
   threshold = ranking at 50th percentile
   (Robust to outliers, unlike average)

3. Rebuild Trie with intelligent promotion
   new_trie = {}
   for each query in top 1M:
     if query.combined_rank > threshold:
       • Add to Trie (Tier 1)
     else:
       • Keep in Redis or Database
   
4. Eviction rule (if new trending queries)
   Tier 2 (100K trending) has reserved slots
   
   IF new trending query needs promotion:
     IF Tier 2 has space:
       → Add immediately
     ELSE if Tier 2 is FULL (100K used):
       → Evict OLDEST trending query
       → Add new trending query
       → Keep newest 100K trending ✓

5. Reset for tomorrow
   UPDATE queries SET short_term_count = 0
   (Tomorrow's trending starts fresh)

Result: Trie updated for tomorrow ✓
```

### Real Example: How Trending Gets Promoted

```
DAY 1 (2 PM):
  User searches "pqrst accounting"
  → Added to Redis (short_term = 1)
  → Ranking = (5 × 1.0) + (1 × 1.0) = 6

DAY 1 (11:59 PM - Batch Job):
  "pqrst accounting" ranking = 6
  Median threshold = 500
  → 6 < 500? NOT promoted to Trie
  → Stays in Redis ✗

DAY 2 (Trending day):
  Users keep searching "pqrst accounting"
  → Redis short_term = 5,000 (very hot!)
  
DAY 2 (11:59 PM - Batch Job):
  "pqrst accounting" ranking = (5 × 1.0) + (5,000 × 1.0) = 5,005
  Median threshold = 500
  → 5,005 > 500? PROMOTED TO TRIE! ✓

DAY 3:
  User types "pqrst"
  → Found instantly in Trie <1ms ✓
  → No database query needed
```

---

## Reserved Capacity Strategy

### Why Tier 2 Has Fixed 100K Slots

```
Option A: Dynamic eviction (add/remove as needed)
  ✗ Variable performance
  ✗ Sometimes cheap (1 removal), sometimes expensive (15K)
  ✗ Unpredictable latency
  ✗ No SLA guarantee

Option B: Reserved capacity (separate tier)
  ✓ Fixed 900K stable + 100K trending
  ✓ Predictable performance
  ✓ 5-10% wasted space << reliable SLA
  ✓ INDUSTRY STANDARD ✓

Reserved capacity thinking:
  • Predictability > Optimization (for fintech!)
  • 99.9% reliability with 100% capacity vs
    99.5% reliability with 95% capacity
  • For SalesPoint: Choose reliability! ✓
```

---

## Storage Calculations

### Trie (In-Memory)

```
Per query reference:
  • Query string: 50 bytes (average)
  • Metadata: 50 bytes
  • Total: 100 bytes per query

For 1M queries:
  1M × 100 bytes = 100MB

Plus node pointers, ranking data:
  → ~1GB total (with overhead)

Acceptable? YES ✓ (fits in modern RAM)
```

### Redis (Recently Popular)

```
Recently clicked obscure queries:
  • Assume 1M cached entries (active users)
  • Each entry: 100 bytes (query + counts)
  • Total: ~100-500MB

TTL: 24 hours (auto-cleanup)
```

### Database (All Queries)

```
Per query:
  • query_text: 50 bytes
  • long_term_count: 8 bytes
  • short_term_count: 8 bytes
  • ranking: 8 bytes
  • metadata: 26 bytes
  • Total: ~100 bytes

For 1B queries:
  1B × 100 bytes = 100GB (manageable)

Indexing: (query_text, combined_rank)
  • Optimize for "LIKE" prefix matching
  • Optimize for ranking sort
```

---

## Bottleneck Analysis

```
READ PATH (User types):
  Bottleneck: None
  • Trie lookup: O(3) = 3 memory accesses
  • Response: <1ms
  • 520K req/sec: EASY ✓

WRITE PATH (User searches):
  Bottleneck: None
  • Redis increment: O(1)
  • Response: <1ms
  • 520K req/sec: EASY ✓

UPDATE PATH (30-min sync):
  Bottleneck: None
  • Batch job: syncs Redis → DB
  • Runs in background (non-blocking)
  • 15B events/day processed off-peak ✓

DAILY BATCH (Recalculate rankings):
  Bottleneck: None
  • Job runs at 11:59 PM (off-peak)
  • Processes all 1B queries
  • Takes ~1 hour (acceptable)
  • No user impact ✓

CONCLUSION: No bottlenecks with proper design!
```

---

## Failure Scenarios

### Scenario 1: Redis Crashes

```
What happens:
  • Lost: Short-term counts from last 30 mins
  • Accessible: Database still has full data (updated 30 mins ago)
  
Impact:
  • Users searching obscure queries: See DB results (slower, but works)
  • RPO (Recovery Point Objective): 30 minutes
  • RTO (Recovery Time Objective): Instant (fallback to DB)
  
Recovery:
  • Restart Redis
  • Rebuild from Database
  • Resume normal operation ✓
```

### Scenario 2: Database Slow/Down

```
What happens:
  • Trie and Redis still work (hot + warm tiers)
  • Only obscure queries slow down
  
Impact:
  • Popular searches: <1ms (Trie) ✓
  • Trending: <5ms (Redis) ✓
  • Obscure: Timeout or fallback
  
Mitigation:
  • Circuit breaker on DB queries
  • Show "No suggestions available" gracefully
  • Don't block user typing ✓
```

### Scenario 3: Traffic Spike

```
Scenario: Celebrity posts about "system design"
  Normal: 100K searches/day
  Spike: 10M searches/day (100x!)

What happens:
  1. Trie already has it (cached)
  2. 99% hit from Trie <1ms
  3. 1% miss from Redis (if any)
  4. NO database queries needed
  5. System absorbs spike easily ✓

Why: Because of caching strategy!
```

---

## Concepts Applied (Days 1-24)

| Day | Concept | Applied |
|-----|---------|---------|
| **Day 3** | Caching | Trie for hot, Redis for warm, DB for cold |
| **Day 7** | Async Jobs | 30-min sync, daily batch updates |
| **Day 10** | Indexing | Compound index on (query_text, combined_rank) |
| **Day 17** | Consistent Hashing | Shard Redis by query (if needed for scale) |
| **Day 18** | Sharding | Partition database by query prefix |

---

## Communication Feedback

**Self-assessed improvement needed:** 6.5/10 → Target: 8.5/10

Key feedback received:
- ✅ Technical thinking: Excellent
- ✅ Problem-solving: Strong (independent discovery of solutions)
- ⚠️ Grammar/structure: Polish needed
- ⚠️ Communication clarity: Work on being concise and structured
- ✅ Self-reflection: Healthy (asking for feedback)

**Action items for Days 25-27:**
1. Organize thoughts BEFORE typing
2. Use clear structure: Problem → Approach → Tradeoff → Reasoning
3. Confident language ("I recommend" not "maybe")
4. Proofread for clarity (5 extra seconds)

---

## Confidence Progress

**Self-assessed: 9-10/10** ⭐⭐⭐

- Day 20: 5/10 (struggling)
- Day 21: 7/10 (improved)
- Day 22: 6/10 (setback on numbers)
- Day 23: 8-9/10 (fanout mastery)
- **Day 24: 9-10/10 (production-grade design)**

**Why confident:**
- ✅ Designed complete system independently
- ✅ Critical thinking on eviction problem
- ✅ Reserved capacity concept
- ✅ Failure scenarios understood
- ✅ Scale handled (520K req/sec)
- ✅ Data structures appropriate (Trie)

---

## What You Discovered Today

1. **Trie is perfect for prefix matching** (O(m) not O(n))
2. **Ranking is a design decision** (weights are tunable)
3. **Hybrid storage matches data distribution** (Pareto principle)
4. **Reserved capacity enables SLA** (predictable > optimal)
5. **Daily batch updates catch trends** (promotion logic)
6. **Tier 2 reserved slots elegantly handle eviction**
7. **No bottlenecks with proper caching strategy**

This is how **Google, Twitter, LinkedIn, and all major search services actually work!**

---

## Next Steps (Days 25-28)

```
Day 25: Rate Limiting Service
  • Learn: Token bucket, sliding window, distributed counters
  
Day 26: Cache Invalidation System
  • Learn: TTL strategies, cache warming, consistency
  
Day 27: Metrics/Monitoring System
  • Learn: Time-series DB, aggregation, alerts
  
Day 28: Phase 1 Complete
  • Continue to Phase 2 (Medium systems)
```

---

## Key Takeaway

> **Good autocomplete design separates concerns by access pattern: Trie for popular (hot), Redis for trending (warm), Database for obscure (cold). Balanced ranking (long-term + short-term) provides great UX. Daily batch promotion catches trends automatically. Reserved capacity in Tier 2 guarantees predictable performance for fintech SLA.**

