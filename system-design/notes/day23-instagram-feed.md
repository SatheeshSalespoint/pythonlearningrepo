# Day 23: Case Study — Instagram Feed Design (Social Media Timeline)

**Date:** 2026-08-15  
**Duration:** ~40 mins  
**Status:** ✅ Complete  
**Difficulty:** Medium  
**Confidence Level:** 8-9/10 (excellent progress!)

---

## The Challenge

Design a **personalized feed system** that shows users posts from people they follow.

**Difference from previous systems:**
- URL Shortener (Day 20): Simple 1-to-1 mapping
- Instagram Feed: Complex 1-to-many **fanout** (one post → millions of timelines)

**Core Problem:** How do you efficiently show a user 20 posts from 50 people they follow without:
- Overloading the database
- Causing slow load times (>500ms)
- Losing data consistency

---

## Scale Estimation

### Feed Reads

```
100M daily active users
Each user checks feed 5 times/day

Calculation:
  100M users × 5 reads/day ÷ 86,400 sec/day = 5,787 reads/sec (average)
  Peak (morning): 3x = ~17,361 reads/sec
  Off-peak: 1/3 = ~1,929 reads/sec

Conclusion: HIGHLY read-heavy system
```

### Posts Created

```
100M users
Each user creates 1 post/day on average

Calculation:
  100M users × 1 post/day ÷ 86,400 sec/day = 1,157 writes/sec (average)

Conclusion: 5x more reads than writes (read-optimized system)
```

### The Fanout Problem

```
Normal User Posts:
  User has 500 followers
  When they post: Update all 500 followers' timelines
  Cost: 500 writes per post

Celebrity Posts:
  Celebrity has 50M followers
  When they post: Update 50M followers' timelines?
  Cost: 50,000,000 writes per post ❌ EXPENSIVE!

Solution: Different strategies for different users
```

---

## The Fanout Decision: Hybrid Approach

### Key Insight

**Not all users are equal in a social network!**

- 99% of users have <100K followers
- 1% of users (celebrities) have 50M+ followers
- Different fanout strategies for different cases

### Fanout-on-Write (Normal Users)

```
When normal user posts:
  POST /api/post
    1. Write post to user's DB
    2. IMMEDIATELY write to all 500 followers' timelines (async)
    3. Return success ✓

When followers read feed:
  GET /api/feed
    1. Query their own timeline (already has the post)
    2. Return instantly ✓

Pros:
  ✅ Followers see post within seconds (good UX)
  ✅ 500 writes is manageable
  ✅ Read is simple and fast

Cons:
  ❌ Expensive for popular users
  ❌ Spike when celebrity posts (millions of writes)
```

### Fanout-on-Read (Celebrities)

```
When celebrity posts:
  POST /api/post
    1. Write post to celebrity's DB only
    2. Return success immediately ✓

When user reads feed:
  GET /api/feed
    1. Query 50 people they follow
    2. For celebrities: Query their DB (fanout-on-read)
    3. For normal users: Read from user's timeline (already there)
    4. Merge all posts, sort by timestamp
    5. Return top 20 ✓

Pros:
  ✅ Post writes instantly (no fanout)
  ✅ Cost is spread across millions of reads
  ✅ Simple for the writer

Cons:
  ❌ Read is slightly more complex (multiple queries)
  ❌ Slightly slower for followers of celebrities
```

### The Hybrid Solution (INDUSTRY STANDARD)

```
Define threshold: 100K followers

IF user.follower_count < 100K:
  Use FANOUT-ON-WRITE
  → Post to all followers' timelines immediately
  
ELSE if user.follower_count >= 100K:
  Use FANOUT-ON-READ
  → Post to celebrity's DB only
  → Followers fetch on read

Result:
  ✅ Normal users: Fast follower experience
  ✅ Celebrities: Fast write, acceptable read speed (with caching)
  ✅ System: Balanced load
  
This is why Twitter/Instagram have "Verified" badges at ~100K followers!
```

---

## Storage Architecture: Hybrid Redis + SQL

### The Problem

```
Timeline is read-heavy (5.8K reads/sec)
Must respond in <500ms
SQL alone is too slow for this volume
```

### The Solution: Redis + SQL

```
REDIS (Hot Cache):
  • Store user's timeline (top 1000 posts)
  • Data structure: Sorted Set (by timestamp)
  • Read latency: <1ms ✓
  • NOT persistent (if crashes, rebuild from SQL)
  
  Key: "timeline:user_123"
  Type: Sorted Set
  Value: [post_id_1, post_id_2, ..., post_id_1000]
  Score: timestamp (for sorting by newest first)

SQL DATABASE (Persistent):
  • Store same timeline data
  • Acts as source of truth
  • Backup if Redis crashes
  • Slower but reliable

SYNC STRATEGY:
  When new post added to timeline:
    1. INSERT into SQL (persistent write)
    2. ZADD to Redis (cache update)
    3. Return success ✓
  
  When Redis misses (rare):
    1. Query SQL
    2. Rebuild Redis from SQL
    3. Return to user
```

### Why This Works

```
Read Pattern (99% of time):
  User reads feed
  → Query Redis (cache HIT)
  → Return instantly (<10ms) ✓
  → No SQL query needed

Read Pattern (1% of time - cache miss):
  Cache miss happens (new user, server restart)
  → Query SQL (slower, but rare)
  → Rebuild Redis
  → Next read hits cache ✓

Write Pattern:
  Post created
  → Write to SQL (consistency guarantee)
  → Update Redis async (eventual consistency)
  → Both kept in sync ✓
```

### Storage Calculations

```
Per user timeline:
  • 1000 posts stored
  • Each post reference: ~100 bytes
  • Total per timeline: ~100KB

For 100M users:
  100M × 100KB = 10TB (if all in memory) - TOO MUCH!
  
Solution: Store only active users' timelines
  • 20M active users with recent timelines
  • 20M × 100KB = 2TB (manageable with modern servers)
  
  Old timelines: Evicted from cache, rebuilt on demand
```

---

## Consistency Model: Differential Consistency

### Key Insight

**Different parts of the system need different consistency levels!**

```
Creator's Timeline (User's own):
  • STRONG consistency required
  • User deletes post → Gone instantly
  
Followers' Timelines:
  • EVENTUAL consistency acceptable
  • Deleted post might appear for hours
  • Eventually cleaned up by async job
```

### Post Deletion Strategy

```
When User deletes a post:

Creator's Timeline:
  1. DELETE immediately from Redis
  2. DELETE immediately from SQL
  3. User sees it gone right away ✓
  4. Followers might still see it temporarily

Followers' Timelines:
  1. Keep in Redis (stale temporarily, acceptable)
  2. Mark as "deleted" in SQL
  3. Async cleanup job (once per day):
     - Query all timelines with deleted posts
     - Remove from Redis
     - Delete from SQL
  4. Eventually removed from all timelines ✓

Result:
  ✅ Creator: Instant deletion (good UX)
  ✅ Followers: Eventually deleted (acceptable for social media)
  ✅ System: Simple, scalable, no thundering herd
```

---

## Architecture Summary

### Complete Feed System

```
WRITE PATH (User posts):
  1. User posts photo + caption
  2. Create post record in SQL
  3. If user has <100K followers:
       → Fanout-on-write to all followers' timelines (async)
       → ZADD to Redis for each follower
  4. If user has >=100K followers:
       → Just write to user's DB
       → Followers will fetch on read
  5. Return success ✓

READ PATH (User checks feed):
  1. GET /api/feed for user_123
  2. Query Redis: ZREVRANGE timeline:user_123 0 19 (top 20)
  3. If cache HIT (99% of time):
       → Return instantly <10ms ✓
  4. If cache MISS:
       → Query SQL for user's timeline
       → Rebuild Redis
       → For each followed celebrity:
         → Query celebrity's posts
         → Merge into timeline
       → Sort by timestamp, return top 20
  5. Return feed to user ✓

DELETE PATH (User deletes post):
  1. User deletes post
  2. DELETE from SQL posts table
  3. DELETE from creator's Redis timeline (instant)
  4. Mark as deleted in timeline records
  5. Async cleanup job:
       → Query all followers' timelines
       → Remove deleted posts from Redis
       → Remove from SQL
  6. Eventually cleaned up ✓
```

### Bottleneck Analysis

```
WRITE PATH:
  Bottleneck: Fanout-on-write (for normal users)
  Solution: Batch async writes, queue service
  Result: ✓ No bottleneck

READ PATH:
  Bottleneck: Multiple queries (for celebrity followers)
  Solution: Redis cache hits 99% of time
  Result: ✓ No bottleneck

DELETE PATH:
  Bottleneck: Async cleanup job
  Solution: Run off-peak (at night)
  Result: ✓ No bottleneck

CONCLUSION: No bottlenecks with proper caching!
```

---

## Key Design Decisions

| Decision | Why | Tradeoff |
|----------|-----|----------|
| **Hybrid fanout** | Normal users see posts fast, celebs don't bottleneck | Complexity handling different user types |
| **Redis + SQL** | Fast reads, persistent storage | Extra infrastructure, sync complexity |
| **Differential consistency** | Creator gets instant feedback, followers accept delay | Temporary stale data |
| **Async cleanup** | Doesn't block deletes, spreads cost | Posts visible briefly after deletion |
| **Sorted Sets in Redis** | O(1) insert, natural timestamp ordering | Memory usage for large timelines |

---

## Concepts Applied (Days 1-23)

| Day | Concept | Applied |
|-----|---------|---------|
| **Day 3** | Caching | Redis cache for timelines |
| **Day 7** | Async jobs | Background fanout, async cleanup |
| **Day 18** | Sharding | Partition timelines by user_id |
| **Day 19** | Replication | Read replicas for SQL backups |
| **Day 5** | CAP Theorem | Chose availability + partition tolerance, eventual consistency for followers |

---

## Confidence Progress

**Self-assessed: 8-9/10** (excellent jump from Day 22's 6/10)

### Why confidence improved:

✅ Making industry-standard architectural decisions  
✅ Understanding differential consistency (advanced concept)  
✅ Thinking about real-world constraints (celebrities)  
✅ Balancing simplicity and scalability  
✅ Connecting previous learning (Days 1-22) to new systems  

### Areas still to master:

⚠️ Deep implementation details (exact Redis commands, etc.)  
⚠️ Performance tuning (cache eviction policies, etc.)  
⚠️ Failure scenarios (cache stampede, replication lag, etc.)  

These will come in Days 24+ as you see more systems!

---

## What You Discovered Today

1. **Fanout is the core challenge** in social networks
2. **Hybrid approaches work best** (not all users are equal)
3. **Differential consistency** (different parts need different guarantees)
4. **Caching is essential** (Redis makes the system work)
5. **Async operations scale** (cleanup, fanout in background)

This is how **Twitter, Instagram, and Facebook actually work!**

---

## Next Steps (Days 24-28)

```
Day 24: Google Autocomplete
  • Learn: Prefix trees, caching, ranking
  
Day 25: Rate Limiting Service
  • Learn: Distributed counters, algorithms
  
Day 26: Cache Invalidation
  • Learn: TTL strategies, consistency
  
Day 27: Metrics/Monitoring System
  • Learn: Time-series DB, aggregation
  
Day 28: Phase 2 Checkpoint
  • Assessment: Ready for Phase 3 (hard systems)?
```

---

## Key Takeaway

> **Good social media design separates the common case (normal users with fanout-on-write) from the edge case (celebrities with fanout-on-read). Hybrid consistency—strong for creators, eventual for followers—provides great UX without overcomplicating the system. Redis caching makes everything fast.**

