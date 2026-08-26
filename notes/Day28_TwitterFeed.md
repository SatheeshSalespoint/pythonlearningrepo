# Day 28: Twitter/Social Media Feed System

**Date:** 2026-08-26  
**Status:** ✅ Done  
**Confidence:** 8/10 (solid hybrid design, practical decisions)  
**Communication Level:** 8.5/10 (maintained from Phase 1)

---

## System Overview

**What:** Real-time social media feed for 100K users with celebrities and normal users  
**Context:** SalesPoint social features (posts, likes, comments, retweets)  
**Scale:**
- 100K users total
- 500M follower relationships (5,000 avg followers/user)
- 512K posts/day (peak hour: 416K posts, normal: 95K posts)
- 740M engagements/day (likes, comments, retweets)
- 5,787 reads/sec (users fetching feeds)
- 578K fanout operations/sec (distributing posts)
- Multi-region (NZ/AUS)

**Core Problem:** How to serve feeds to 100K users while handling millions of posts and engagements efficiently, with acceptable cross-region latency.

---

## Bottleneck Identified

### Primary Bottleneck: Fanout Speed & Consistency Trade-off

**The Challenge:**
```
Write-on-Fanout (Push):
  • Each post fanouts to followers (578K ops/sec)
  • Followers see posts immediately (strong consistency)
  • Database must handle massive write volume
  → Bottleneck: Write throughput

Read-on-Demand (Pull):
  • Write once to Posts table (1 write/sec)
  • Followers query when checking feed (cheap writes)
  • Followers see posts with 1-2 second delay
  → Bottleneck: Query efficiency

Consistency Gap:
  • User sees their post immediately
  • Followers see it with delay (eventual consistency)
  • Cross-region users see it even later (1-2 seconds)
```

**Solution:** Hybrid approach with different strategies for different user types

---

## Design Decisions

### Decision 1: Architecture Strategy (Pull-on-Demand)

```
NORMAL USERS (< 5K followers):
  • Use PULL model (read-on-demand)
  • Efficient, manageable scale
  
CELEBRITY USERS (100K+ followers):
  • Still use PULL model (same Posts table)
  • But with different indexing
  • Reason: Avoid 100K writes/sec explosion
```

**Why Pull Over Push:**
- Push: 578K writes/sec at peak (risky threshold)
- Pull: 1-2 writes/sec (safe, scalable)
- Trade-off: 1-2 second delay acceptable

---

### Decision 2: Data Storage

#### Posts Table (Central)

```
Schema:
  post_id (PK): UUID
  author_id: user_id (indexed)
  content: text/image/video (1KB avg)
  timestamp: datetime (indexed)
  region: NZ/AUS (for replication tracking)

Storage:
  512K posts/day × 1KB = 512MB/day
  30-day retention: 15.36GB
  
Indexing:
  • (author_id, timestamp DESC) - for user's profile
  • (timestamp DESC) - for global timeline
  • (region, timestamp) - for regional replication
```

---

#### Engagements Table (Separate)

```
Schema:
  engagement_id (PK): UUID
  post_id (FK): indexed
  user_id: who engaged
  type: 'like' | 'comment' | 'retweet'
  content: text (for comments only)
  timestamp: datetime

Storage:
  740M engagements/day × 200 bytes = 148GB/day
  30-day retention: 4.44TB
  
Indexing:
  • (post_id, type, timestamp DESC) - for fetching likes/comments
  • (user_id, timestamp DESC) - for user's activity feed

Optimization:
  • Lazy loading (return top 100 comments, not all)
  • Pagination for large posts
```

---

### Decision 3: Engagement Aggregation Strategy

```
LIKES (Stale acceptable):
  • Count aggregated every 1 HOUR
  • Cost: 24 batch jobs/day (cheap)
  • Freshness: 0-60 minutes stale
  • Method: SELECT COUNT(*) FROM engagements WHERE post_id=X AND type='like'
  
COMMENTS (Fresher needed):
  • Aggregated every 5 MINUTES
  • Cost: 288 batch jobs/day (moderate)
  • Freshness: 0-5 minutes stale
  • Method: Full query or cached list of recent 100
  
RETWEETS (Similar to likes):
  • Aggregated every 1 HOUR
  • Same as likes (count-based)

Storage:
  • Like counts + retweet counts: Cached in Redis
  • Comment list: Stored in Engagements table (lazy loaded)
  • Update frequency: Likes/retweets 1x/hour, comments 1x/5min
```

---

### Decision 4: Feed Read Operation (Pull Model)

```
User opens their feed:

QUERY:
  SELECT p.*, 
         (SELECT COUNT(*) FROM engagements WHERE post_id=p.post_id AND type='like') as like_count,
         (SELECT COUNT(*) FROM engagements WHERE post_id=p.post_id AND type='retweet') as retweet_count
  FROM Posts p
  WHERE p.author_id IN (SELECT following_id FROM follows WHERE follower_id = user_id)
  ORDER BY p.timestamp DESC
  LIMIT 50

OPTIMIZATION:
  • Use Redis cache for like/retweet counts (updated every 1 hour)
  • Comments fetched separately (lazy loading)
  • Pagination: Load 50 posts, show top comments per post
  
LATENCY:
  • Cold: 200-500ms (first load, query cache miss)
  • Warm: 50-100ms (subsequent loads, cache hit)
```

---

### Decision 5: Regional Replication Strategy (Hybrid)

```
Architecture:
  ├─ NZ Region
  │  ├─ Posts table (primary for NZ)
  │  ├─ Engagements table (primary for NZ)
  │  └─ Replication service
  │
  └─ AUS Region
     ├─ Posts table (replica from NZ)
     ├─ Engagements table (replica from NZ)
     └─ Receives updates via batch replication

Replication Strategy (HYBRID):
  
  POSTS & COMMENTS: Replicate every 5 MINUTES
    • When NZ user posts, visible in NZ instantly
    • Replicate to AUS, visible in AUS after 5 minutes
    • Rationale: Comments need freshness, 5min acceptable
  
  LIKES & RETWEETS: Replicate every 1 HOUR
    • When NZ user likes, count updated in NZ instantly
    • Replicate to AUS, count visible in AUS after 1 hour
    • Rationale: Counts can be stale, save bandwidth
    
Timeline:
  T=0s: User in NZ posts
  T=1s: Post visible in NZ (instant)
  T=5m: Post visible in AUS (5-minute replication)
  T=60m: Like counts updated in AUS (1-hour replication)
```

---

## Complete System Architecture

### Layer 1: Write Path (User Creates Post)

```
User_A in NZ creates post:
  
  1. App validates post (rate limiting, content)
  2. Write to NZ Posts table
     INSERT INTO posts (author_id, content, region, timestamp)
  3. Immediately visible to User_A (strong consistency)
  4. Queue for replication to AUS
  5. Return success to user
  
Result:
  • 1 write operation (fast)
  • User sees immediately
  • NZ followers see immediately
  • AUS followers see after 5 minutes (eventual)
```

### Layer 2: Engagement Path (User Likes Post)

```
User_B in NZ likes post:
  
  1. Write to Engagements table
     INSERT INTO engagements (post_id, user_id, type='like', timestamp)
  2. Increment like_count cache (Redis)
  3. Return success to user
  
Background (every 1 hour):
  4. Aggregate: COUNT all likes from engagements table
  5. Update Posts.like_count
  6. Replicate to AUS
  
Result:
  • 1 write operation (fast)
  • Like count updated within 1 hour
  • Counts replicated to AUS after 1 hour
```

### Layer 3: Read Path (User Opens Feed)

```
User_C in NZ opens feed:
  
  1. Query: GET posts from people I follow
     SELECT * FROM posts WHERE author IN (following_list)
  2. For each post, fetch engagement counts (from cache)
  3. For comments: Lazy load (fetch top 100 on demand)
  4. Return 50 posts with engagement counts
  
Latency:
  • Cold (cache miss): 200-500ms
  • Warm (cache hit): 50-100ms
  
Result:
  • Single query (efficient)
  • Engagements from cache (fast)
  • Comments loaded on click (lazy)
```

### Layer 4: Aggregation & Replication (Background Jobs)

```
Every 5 minutes:
  • Replicate posts & comments to AUS
  • Query: SELECT * FROM posts WHERE region='NZ' AND timestamp > last_sync
  • Write to AUS posts table
  
Every 1 hour:
  • Aggregate like counts
  • Aggregate retweet counts
  • Replicate to AUS
  • Update cache in both regions
  
Cost:
  • 5-min job: ~5 seconds runtime (cheap)
  • 1-hour job: ~30 seconds runtime (minimal)
```

---

## Storage & Performance Calculations

### Storage Breakdown

```
Posts Table:
  • 512K posts/day × 1KB = 512MB/day
  • 30-day retention: 15.36GB (hot)
  • Archive: S3 (cold storage)

Engagements Table:
  • 740M engagements/day × 200 bytes = 148GB/day
  • This is HUGE, needs optimization
  • Solution: Archive old engagements (>30 days) to S3
  • Keep only recent engagements in DB (e.g., last 7 days)
  • Recent engagements: 148GB × 7 = ~1TB (manageable)

Cache (Redis for like counts):
  • 512K posts × 8 bytes (count) = 4MB/day
  • Very small, in-memory

Total Active Storage:
  • Posts: 15GB
  • Engagements: 1TB (7-day window)
  • Cache: 4MB
  ───────────────
  • Total: ~1TB (reasonable for this scale)
```

---

## Bottleneck Solutions

| Bottleneck | Root Cause | Solution |
|-----------|-----------|----------|
| **Fanout write explosion** | 578K writes/sec | Use pull (read-on-demand) instead of push (write-on-fanout) |
| **Engagement storage bloat** | 148GB/day engagements | Archive old engagements, keep recent in DB |
| **Like count freshness** | Query count every read | Cache counts, update batch every 1 hour |
| **Comment latency** | Stale comments frustrate users | Replicate comments every 5 minutes (not 1 hour) |
| **Cross-region delay** | Global users see posts slowly | Accept 1-5 minute delay for cross-region (eventual consistency) |
| **Query efficiency** | Querying millions of posts slow | Index by (author_id, timestamp), use cache for engagement counts |

---

## Key Design Decisions & Trade-offs

| Decision | Choice | Why | Trade-off |
|----------|--------|-----|-----------|
| **Architecture** | Pull (read-on-demand) | Avoid 578K writes/sec explosion | 1-2 second delay for followers |
| **Storage** | Separate engagements table | Organized, indexed efficiently | Extra queries needed for engagement counts |
| **Like aggregation** | Batch every 1 hour | Cheap, acceptable staleness | Like counts 0-60 mins behind reality |
| **Comment aggregation** | Batch every 5 minutes | Fresh comments for UX | More expensive (288 jobs/day) |
| **Regional replication** | Hybrid (5min posts, 1hr likes) | Balance freshness + cost | Cross-region inconsistency for 1-5 minutes |
| **Engagement retention** | 7-day hot + archive to S3 | Manage storage (1TB vs 4TB) | Old engagements query slower (S3 only) |

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Pull-on-demand architecture** | 9/10 — Solved write bottleneck |
| **Engagement aggregation strategy** | 8/10 — Balanced cost vs freshness |
| **Regional replication (hybrid)** | 8/10 — Practical, accepts eventual consistency |
| **Storage calculations** | 8/10 — Reasonable estimates |
| **Indexing strategy** | 7/10 — Basic understanding, could optimize further |
| **Cache strategy** | 8/10 — Redis for counts is solid |

**Overall Day 28:** 8/10 ✅

---

## Learning Outcomes

### Architecture Thinking
✓ Identified fanout bottleneck (578K writes/sec)  
✓ Chose pull over push (trade-off between consistency and scale)  
✓ Hybrid strategy for different user types (normal vs celebrity)  

### Scale-Aware Design
✓ Storage calculations (15GB posts, 1TB engagements)  
✓ Engagement rate estimation (10% of followers)  
✓ Batch job cost analysis (5min vs 1hour)  

### Consistency Trade-offs
✓ Accepted eventual consistency for scale (1-2 second delay)  
✓ Regional replication strategy (hybrid timing)  
✓ Different freshness for different data types (likes vs comments)  

### Production Thinking
✓ Archive strategy (keep recent, cold storage old)  
✓ Lazy loading (comments on demand, not all at once)  
✓ Caching strategy (aggregated counts in Redis)  

---

## Phase 2 Progress

| Day | System | Confidence | Communication |
|-----|--------|-----------|-----------------|
| Day 27 | Metrics & Monitoring | 8/10 | 8.5/10 ✅ |
| **Day 28** | **Twitter Feed** | **8/10** | **8.5/10** ✅ |

**Maintained communication at 8.5/10** while designing complex system ✅

---

## Next: Day 29 — Messaging Queue

**What's next:** Reliability, ordering, deduplication  
**Bottleneck preview:** How to ensure messages don't get lost or duplicated at scale?

**Status:** ✅ Day 28 Complete — Ready for Day 29  
**Momentum:** Strong, applying phase 1 framework to medium-difficulty systems
