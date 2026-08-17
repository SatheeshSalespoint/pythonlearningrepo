# Day 22: Case Study — Analytics-Heavy URL Shortener (Bit.ly Style)

**Date:** 2026-08-14  
**Duration:** ~45 mins  
**Status:** ✅ Complete  
**Difficulty:** Easy (variant of Day 20)

---

## The Challenge

Design a **URL shortener with detailed analytics**, like Bit.ly.

**Difference from Day 20:**
- Day 20: Simple redirect (read-heavy)
- Day 22: Same, PLUS track detailed analytics per link

**User Requirements:**
- Create short URLs
- Redirect to original URL
- **NEW:** Show real-time dashboard with click analytics
  - Total clicks over time
  - Clicks by country
  - Clicks by device (mobile vs desktop)
  - Breakdown by referrer (optional)

---

## Problem Statement

Adding analytics to a URL shortener introduces a **new bottleneck:**

```
Day 20 Problem: How to redirect 200M clicks/day efficiently?
Day 22 Problem: How to track 200M analytics events AND 
                show dashboard queries in real-time?
```

**The Tension:**
- Storing every click as raw data = huge storage (10GB/day)
- Querying raw data for dashboards = SLOW (billions of rows)
- Need pre-computed aggregates, but how often to update?

---

## Scale Estimation

### Reads (Clicks)

```
200M clicks/day = 200,000,000 clicks
Per second: 200M ÷ 86,400 = ~2,315 clicks/sec (average)

Peak (morning): 3x average = ~6,945 clicks/sec
Off-peak: 1/3 average = ~770 clicks/sec

Conclusion: High read volume, distributed throughout day
```

### Writes (Analytics Events)

```
Every click = 1 analytics event
200M analytics events/day = 2,315 events/sec

Plus: 20M new links/day = 231 link creates/sec

Total writes: 2,315 + 231 = ~2,546 writes/sec
```

---

## Storage Calculation

### Raw Events Table

```
Per event (one click):
  • timestamp: 8 bytes
  • IP address: 15 bytes
  • device_type (enum): 1 byte
  • country (enum): 1-2 bytes
  • city (VARCHAR): 20-30 bytes
  • click_sequence_num: 4 bytes
  ≈ 50 bytes per event

Daily storage:
  200M events × 50 bytes = 10,000,000,000 bytes = 10GB/day
  
Monthly storage:
  10GB/day × 30 days = 300GB/month (hot storage)
  
Yearly storage:
  10GB/day × 365 = 3.65TB
```

### Problem: Query Performance

```
If store ALL raw events in one DB:
  • 3.65TB of data
  • Querying for dashboards = scan billions of rows
  • VERY SLOW ❌

Solution: Don't keep all in one DB!
```

---

## Architecture Solution: Time-Based Partitioning + Aggregation

### Strategy

```
WRITE PATH (Every click):
  1. User clicks link
  2. Log raw_event to raw_events table (current month DB)
  3. Redirect immediately ✓
  
AGGREGATION (Once per day, at midnight):
  1. Query raw_events table (current month only)
  2. GROUP BY hour, country, device_type
  3. SUM(clicks) for each group
  4. INSERT into aggregate_table
  5. Delete processed raw events
  
MONTHLY ROTATION:
  1. Current month: hot DB (raw_events + aggregate_table)
  2. Previous months: archive to blob storage (cheap)
  3. Every month: create new DB for next month
  
READ PATH (Dashboard):
  1. Query aggregate_table (pre-computed, small)
  2. Show aggregated data (24 hours old, acceptable)
```

---

## Decision: Hourly vs Daily Aggregation

### Comparison

| Aspect | Hourly | Daily |
|--------|--------|-------|
| **Frequency** | Run every hour | Run once per day |
| **Rows per link (7 days)** | 98,280 | 4,095 |
| **Detail level** | Hour-by-hour | Day-by-day |
| **Data freshness** | 1 hour old | 24 hours old |
| **Complexity** | Higher | Lower |
| **Worker runs** | 24 times/day | 1 time/day |

### Decision: DAILY is better ✅

**Why:**
- URL shortener users care about daily totals, not hourly
- 24x fewer rows (4k vs 98k per link)
- Simpler worker process
- Acceptable 24-hour delay for analytics

**Tradeoff accepted:**
- Less detail (daily only)
- Simpler system (worth it)

---

## Aggregate Table Schema

```sql
CREATE TABLE aggregate_analytics (
  id BIGINT PRIMARY KEY,
  link_id VARCHAR(10),
  date DATE,
  country VARCHAR(2),
  device_type ENUM('mobile', 'desktop', 'tablet'),
  click_count INT,
  INDEX(link_id, date)
);

Example row:
  link_id: "cv5"
  date: "2026-08-14"
  country: "nz"
  device_type: "mobile"
  click_count: 15230
```

### Why These Fields Only?

```
INCLUDE:
  ✓ link_id (which link)
  ✓ date (time dimension)
  ✓ country (geographic insight)
  ✓ device_type (mobile vs desktop = key metric)
  ✓ click_count (the metric)

EXCLUDE:
  ✗ referrer (not actionable for dashboard)
  ✗ browser type (too granular, not useful)
  ✗ exact city (country level sufficient)
```

---

## Storage Analysis

### Aggregate Table (Daily)

```
Per day, for ONE link:
  195 countries × 3 devices = 585 rows

For 20K active links:
  20K × 585 = 11.7M rows/day

Over 7 days: 81.9M rows
Over 30 days (1 month): 351M rows ≈ 20GB

Total with raw_events: ~300GB + 20GB = ~320GB hot storage
```

### Monthly Rotation Benefits

```
Current month DB: 320GB (manageable)
Previous 11 months: archived to blob storage (~$10/month)

Without rotation:
  3.65TB in one DB = slow queries, expensive, hard to manage

With rotation:
  ✓ Current month: fast queries
  ✓ Old months: cheap archive
  ✓ Compliance: keep 1+ year of data
```

---

## Query Performance & Indexing

### Dashboard Query Example

```sql
SELECT device_type, SUM(click_count) as total_clicks
FROM aggregate_analytics
WHERE link_id = 'cv5' AND date >= NOW() - INTERVAL 7 DAY
GROUP BY device_type;

Execution plan:
  1. Use index (link_id, date) to find cv5's rows
  2. Filter by date range (last 7 days = 7 rows per device)
  3. Group by device_type
  4. SUM click_count
  
Result: 3 rows (mobile, desktop, tablet totals) ✓ FAST
```

### Index Strategy

```
Index: (link_id, date, country)
  Why order matters:
    • link_id first (most selective, filters to one link)
    • date second (narrows time range)
    • country last (if needed in WHERE clause)
    
Result: Queries are millisecond-fast ✓
```

---

## Bottleneck Analysis

```
WRITE PATH:
  • Raw events: 2,315/sec to current month DB
  • Bottleneck: None (modern DBs handle this easily)
  
AGGREGATION PATH:
  • Worker runs once/day
  • Processes 200M raw events
  • Bottleneck: None (batch job, runs off-peak)
  
READ PATH:
  • Dashboard queries on aggregate_table
  • Small dataset (351M rows/month)
  • Index present (link_id, date)
  • Bottleneck: None ✓

CONCLUSION: No bottleneck with this design!
```

---

## Consistency Model: Eventual Consistency

```
Level: EVENTUAL CONSISTENCY

Timeline:
  T=0:     User clicks link
  T=0ms:   Raw event logged, user redirected ✓
  T=24h:   Aggregates updated (daily job runs)
  T=24h:   Dashboard shows updated data

Acceptable? ✅ YES
  • Analytics don't need real-time accuracy
  • 24 hours is standard for analytics systems
  • Users understand dashboards aren't live

Tradeoff: Simplicity > Real-time
```

---

## Failure Scenarios

### Scenario 1: Aggregation Worker Crashes

```
What happens:
  • Worker fails mid-aggregation
  • Some aggregates not computed
  • Dashboard shows partial data

Recovery:
  1. Restart worker
  2. Re-run aggregation (idempotent)
  3. Data not lost (raw_events still exist)
  
Prevention: Monitoring + alerting on worker health
```

### Scenario 2: Raw Events DB Crashes (Current Month)

```
What happens:
  • Lose today's raw events + aggregates
  • Yesterday's data is safe (already aggregated)

Recovery:
  1. Restore from backup (assume 4-hour RPO)
  2. Lose at most 4 hours of analytics
  3. Redirect still works (different DB)

Prevention:
  ✓ Daily backups of raw_events
  ✓ Replication (master-slave)
  ✓ Keep 1 month of raw data before archiving
```

### Scenario 3: Aggregate Table Query Spike

```
What happens:
  • 1000s of users query dashboard simultaneously
  • Database gets slow
  • Queries timeout

Mitigation:
  ✓ Cache aggregate results in Redis (1-hour TTL)
  ✓ Read replicas for aggregate_table
  ✓ Circuit breaker: if slow, serve cached version
  
Result: Graceful degradation ✓
```

---

## Critical Thinking Lessons

### Calculation Accuracy

**Mistake made:**
```
200M clicks × 50 bytes = 8GB (WRONG)
Correct: 10GB

Why mistakes happen:
  • 200M = 200,000,000 (easy to lose zeros mentally)
  • Use calculator, don't do math in head
```

**Best practices:**
```
1. Write out full numbers: 200,000,000 not 200M
2. Use online calculator: "200000000 * 50"
3. Verify unit conversion: 10,000,000,000 bytes = 10 GB
4. Sanity check: "10GB/day sounds reasonable for 200M clicks"
```

### Challenging Assumptions

**Question raised:** "Why 195 countries?"

**Better approach:**
```
Don't accept numbers blindly!
Ask: Is this global or regional?
  • Global → ~195 countries
  • Regional (NZ/AUS) → 2 countries
  
This CHANGES the design!

Lesson: Always question scale assumptions
```

---

## Key Design Decisions Summary

| Decision | Why | Tradeoff |
|----------|-----|----------|
| **Daily aggregation** | Simpler than hourly | 24-hour delay vs real-time |
| **Time-based partitioning** | Keeps hot DB small | Need to manage multiple DBs |
| **Pre-computed aggregates** | Dashboard queries fast | 24-hour lag before data appears |
| **Archive old months** | Cost optimization | Need restore process for historical queries |
| **Daily batch worker** | Simple scheduling | One job, once/day |
| **Eventual consistency** | Acceptable for analytics | Not real-time |

---

## What This Teaches You

### Concepts Applied (from Days 1-21)

| Day | Concept | Applied |
|-----|---------|---------|
| **Day 3** | Caching | Cache dashboard results in Redis |
| **Day 7** | Async jobs | Background worker for aggregation |
| **Day 18** | Denormalization | Pre-computed aggregate table |
| **Day 18** | Partitioning | Time-based sharding (monthly) |
| **Day 19** | Replication | Read replicas for dashboard queries |

### Core Skills Practiced

✅ Scale estimation (reads, writes, storage)  
✅ Bottleneck identification (none in this design!)  
✅ Tradeoff analysis (hourly vs daily, real-time vs eventual)  
✅ Critical thinking (questioning assumptions)  
✅ Failure scenarios (what breaks, how to recover)  
✅ Index strategy (query optimization)  
✅ Storage optimization (monthly rotation, archival)  

---

## Confidence Assessment

**Self-rated: 6/10**

This is HEALTHY progress because:
- Understanding core concepts ✅
- Making reasonable design choices ✅
- Identifying tradeoffs ✅
- Areas to improve:
  - Number calculations (use calculator)
  - Challenging own assumptions (good job on this!)

**By Day 28 (end of Phase 2):** Confidence will be 8-9/10

---

## Next Steps (Days 23-28)

```
Day 23: Instagram Feed
  • Learn: Fanout, denormalization, timeline consistency
  
Day 24: Google Autocomplete
  • Learn: Trie data structures, prefix matching, caching
  
Day 25: Rate Limiting Service
  • Learn: Distributed counters, Redis, algorithms
  
Day 26: Cache Invalidation
  • Learn: TTL strategies, cache warming, consistency
  
Day 27: Metrics/Monitoring System
  • Learn: Time-series DB, aggregation, alerting
  
Day 28: Phase 2 Checkpoint
  • Assess readiness for Phase 3 (hard systems)
```

---

## Key Takeaway

> **Good system design balances simplicity and performance. Eventual consistency is acceptable for non-critical data. Time-based partitioning scales storage without sacrificing query performance. Always use a calculator and question your assumptions.**

