# Day 20: Case Study — Designing a URL Shortener

**Date:** 2026-08-12  
**Duration:** ~60 mins (full design walkthrough with Q&A)  
**Status:** ✅ Complete

---

## The Problem

Design a URL shortening service like **bit.ly** or **TinyURL** that:
- Takes long URLs and creates short links
- Redirects short links back to original URLs  
- Handles millions of users
- Optimized for high read volume (users clicking links)

---

## Step 1: Traffic Estimation (Critical Foundation)

### Daily Volume
```
10M daily active users
Each user creates 2 short links/day = 20M writes/day
Each short link clicked 10 times/day = 200M reads/day

Ratio: Reads >> Writes (10:1)
→ Optimize system for READS, not writes
```

### Requests Per Second (Peak)

**Writes:**
```
20M writes/day ÷ 86,400 sec/day = ~231 writes/sec (average)
Peak (3-5x): ~1,150 writes/sec
```

**Reads:**
```
200M reads/day ÷ 86,400 sec/day = ~2,315 reads/sec (average)
Peak (3-5x): ~11,575 reads/sec
```

### Storage Requirements

```
Per entry:
  • Original URL: ~1000 bytes (VARCHAR)
  • Short URL: ~10 bytes (VARCHAR)
  • user_id: 8 bytes (BIGINT)
  • created_at: 8 bytes (TIMESTAMP)
  • Metadata: ~10 bytes
  = ~1,036 bytes per entry

20M entries/day × 1,036 bytes = ~20.7 GB/day
Yearly: ~7.5 TB
```

---

## Step 2: Shard Key Selection (Day 18 Applied)

### Option 1: Shard by user_id ❌
```
Pro: User's URLs on one shard (no cross-shard joins for user dashboard)
Con: Clicking a link = access from different user
     Need to query ALL shards to find the short_url
     → Slow! ❌
```

### Option 2: Shard by short_url ✅ (CHOSEN)
```
Pro: ✓ Clicking short_url → hash determines shard immediately
     ✓ Reads distributed across shards (scales)
     ✓ No fan-out to multiple shards

Con: ⚠️ User's URLs scattered across shards
     (Solved with separate analytics DB)
```

**Decision:** Shard by short_url because reads >> writes.

---

## Step 3: Primary Key Generation

### Challenge
Generate unique, collision-free short URLs without central bottleneck.

### Option A: Random + Retry ❌
```
Generate random 10-char string
Check if exists
If collision → retry
Problem: Retries slow, collisions possible
```

### Option B: Central ID Generator ❌
```
Central service generates IDs 1, 2, 3...
Convert to base62: abc123
Problem: Single point of failure, bottleneck
```

### Option C: User ID + Sequence ✅ (CHOSEN)
```
short_url = base62(user_id) + base62(sequence)

Example:
  user_id=123, seq=1 → base62(123) + base62(1) = "cv1"
  user_id=123, seq=2 → "cv2"
  user_id=456, seq=1 → "ho1"

Pros: ✓ Distributed (no central generator)
      ✓ Guaranteed unique (user_id alone ensures uniqueness)
      ✓ No collisions
      ✓ Simple to implement
      
Con: ⚠️ Predictable (acceptable for URL shortener)
```

---

## Step 4: Database Schema

```sql
CREATE TABLE urls (
  short_url VARCHAR(10) PRIMARY KEY,
  original_url VARCHAR(1000) NOT NULL,
  user_id BIGINT NOT NULL,
  created_at TIMESTAMP,
  click_count INT DEFAULT 0,
  INDEX(user_id)  -- for analytics sync
);

-- Distributed across shards
-- Shard determined by: hash(short_url) % num_shards
```

---

## Step 5: Complete Architecture

### Write Flow (User Creates Short URL)

```
User Request: "Create short URL for https://example.com/article"
       ↓
App Server:
  1. Generate short_url = base62(user_id) + base62(sequence)
     Example: "cv5"
  2. Determine shard = hash("cv5") % num_shards
  3. Write to shard:
     INSERT urls (short_url, original_url, user_id, created_at)
     VALUES ("cv5", "https://example.com/article", 123, NOW())
       ↓
Database Shard (async):
  4. Return response immediately ✓
  5. Async job syncs to Analytics DB (for user dashboard)
       ↓
Response: "Your short URL: bit.ly/cv5"
```

**Bottleneck:** DB write to shard (unavoidable, but fast with sharding)  
**Optimization:** Async analytics sync (doesn't block response)

---

### Read Flow (User Clicks Short URL)

```
User clicks: bit.ly/cv5
       ↓
App Server:
  1. Check Redis Cache for key "cv5"
       ↓
  IF CACHE HIT (99% of time):
    → Return original_url instantly ✓
       ↓
  IF CACHE MISS (1% of time):
    2. Hash("cv5") determines shard
    3. Query read replica of that shard:
       SELECT original_url FROM urls WHERE short_url = "cv5"
    4. Cache the result in Redis (for next time)
    5. Increment click_count (async, non-blocking)
       ↓
Response: Redirect to original_url
```

**Optimization Stack:**
```
Layer 1: Redis Cache (99% hit rate)
         → instant response

Layer 2: Read Replicas per Shard (if cache miss)
         → distribute reads, no bottleneck

Layer 3: Cache Lock
         → prevent cache stampede on popular URLs
```

---

## Step 6: Secondary Query — User Dashboard

**Problem:** User wants to see "all my short URLs"  
But short URLs are sharded by short_url, not user_id!

**Solution: Separate Analytics Database** (denormalization, Day 18)

```
Main Database (sharded by short_url):
  • Optimized for: "Get original_url for short_url"
  • Fast, distributed ✓

Analytics Database (NOT sharded):
  Table: user_urls
    user_id | short_url | original_url | created_at | clicks
  
  • Optimized for: "Get all URLs for user_id"
  • Updated via background job (async)
  • Fresh enough for dashboard (eventual consistency)
       ↓
Architecture:
  Main Shard 1 ──┐
  Main Shard 2 ──┤ Background Job (hourly) ──→ Analytics DB
  Main Shard 3 ──┘
```

**Tradeoff:** Analytics DB is eventually consistent (1 hour lag acceptable for dashboard).

---

## Step 7: Handling Failures

### Scenario: Main Shard Leader Fails

**During Failure:**
```
Before: Leader (accepts writes & reads)
        ↓ replicates
        Follower 1 (200ms lag)
        Follower 2 (500ms lag)

Leader crashes 💥

Immediately:
  • Reads: Continue on Followers ✓
  • Writes: Blocked (no leader) ⚠️

Recovery (~30-60 seconds):
  1. Detect leader failure (health check timeout)
  2. Promote most-caught-up Follower (Follower 1)
  3. Redirect writes to new Leader
  4. Resume writes ✓
```

**User Impact:**
- Clicks still work (reads on followers) ✓
- Creating new short URLs blocked briefly (~1 min)
- Then resumes ✓

---

## Step 8: Handling Scale

### Scenario: One URL Goes Viral (1M clicks/sec)

**The Problem:**
```
Normal short URL: 10k clicks/sec
Viral short URL: 1M clicks/sec (100x spike!)
```

**The Solution:**
```
Layer 1: Redis Cache absorbs 99%
         1M clicks → 10k cache misses/sec

Layer 2: Read Replicas on that shard
         Read replicas = 3-5 copies of data
         Distribute 10k misses across replicas
         Each replica: ~2k queries/sec (easy) ✓

Layer 3: Cache Lock
         If cache stampedes (multiple cache misses),
         only ONE request queries DB,
         others wait for cache update
         → prevent thundering herd ✓
```

**Result:** 1M QPS handled with read replicas + caching ✓

---

## Step 9: Edge Cases & Gotchas

### Edge Case 1: Duplicate URL Shortening
```
User creates short URL twice for same original URL:
  Request 1: "Create short for https://example.com/article"
  Request 2: "Create short for https://example.com/article" (again)

Options:
  A) Create two different short URLs (simpler) ✓
  B) Check if URL exists, return existing short URL (save storage)

Recommendation: Option A (simpler, acceptable for most use cases)
```

### Edge Case 2: Short URL Collision
```
With base62(user_id) + base62(sequence):
  user_id=1, seq=1 → "11"
  user_id=2, seq=0 → "20"

Guaranteed unique? YES ✓
(Different user_ids ensure different prefixes)
```

### Edge Case 3: Sequence Overflow
```
If one user creates too many URLs:
  user_id=123, seq=1
  user_id=123, seq=2
  ...
  user_id=123, seq=62^5 (max for 5 chars)

With 10-char total:
  base62(123) = "cv" (2 chars)
  Remaining for sequence = 8 chars
  Capacity: 62^8 = 218 trillion URLs per user ✓

Practically infinite for any single user
```

---

## Key Design Decisions Summary

| Decision | Why |
|----------|-----|
| **Shard by short_url** | Reads >> writes; optimize for read access |
| **User ID + sequence** | No central bottleneck, guaranteed unique |
| **Redis cache** | 99% of reads served instantly |
| **Read replicas** | Handle cache misses without bottleneck |
| **Separate analytics DB** | User dashboard queries without affecting main path |
| **Async analytics sync** | Don't block write response |
| **Cache lock** | Prevent stampede on viral URLs |

---

## Key Takeaway

> **URL shorteners are READ-HEAVY systems. Optimize for reads: shard by content (short_url), cache aggressively (Redis + cache lock), replicate for scale (read replicas). Handle secondary queries (user dashboard) with separate analytics DB. Failover is transparent for reads, brief downtime for writes.**

---

## Questions Learned Today

1. ✅ Traffic estimation (reads vs writes)
2. ✅ Shard key selection based on access patterns
3. ✅ Primary key generation (distributed, collision-free)
4. ✅ Caching strategy (cache lock, cache stampede prevention)
5. ✅ Secondary queries (analytics DB, denormalization)
6. ✅ Failure scenarios and recovery
7. ✅ Handling viral content (1M QPS surge)
8. ✅ Edge cases and gotchas

---

## What This Case Study Demonstrates

Applied concepts from Days 1-19:
- **Day 18 (Sharding):** Shard by short_url, not user_id
- **Day 19 (Replication):** Read replicas, failover
- **Day 17 (Consistent Hashing):** Shard determination, cache lock
- **Day 8 (Rate Limiting):** Cache stampede prevention
- **Day 3 (Caching):** Redis cache, cache invalidation
- **Days 1-2 (Scaling):** Horizontal scaling via sharding + replicas
- **Day 7 (Async):** Background jobs for analytics sync

This is a **complete system design** applying everything learned.
