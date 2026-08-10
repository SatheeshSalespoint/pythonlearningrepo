# Day 19: Replication — Leader/Follower

**Date:** 2026-08-11  
**Duration:** ~45 mins (with Q&A)  
**Status:** ✅ Complete

---

## Core Concept

**Replication** = copying data from one server (Leader) to multiple servers (Followers). 

**Leader-Follower Pattern:**
- **Leader:** Accepts all writes, sends changes to Followers
- **Followers:** Read-only copies of Leader data

**Why:** Scale reads (distribute across followers) + redundancy (backup if Leader fails).

---

## The Problem: Single Server Bottleneck

```
Single server issues:
  • No redundancy → if crashes, data gone
  • Read bottleneck → maxes out at ~1000 QPS
  
Solution: Replicate to multiple servers
```

---

## Leader-Follower Architecture

### How It Works

```
Write flow (inserts/updates):
  → Always go to LEADER
  → Leader writes locally
  → Leader sends change to all Followers

Read flow (selects):
  → Can go to Leader OR Followers
  → Spread reads across N servers (scales!)
```

### Capacity Scaling

```
Single server: 1000 QPS max
Leader-Follower (3 servers):
  • Writes: 1000 QPS (Leader only)
  • Reads: 3000 QPS (spread across 3 servers) ✓
```

---

## The Gotcha: Replication Lag

**Replication Lag** = delay between write on Leader and when data appears on Followers.

Typical: 100ms-1s (network latency + processing time)

### Problem: Inconsistent Reads

```
Timeline:
T=0ms:    User updates email to alice@new.com → LEADER
T=0-100ms: Replicating to Followers
T=50ms:   User checks profile on FOLLOWER
T=50ms:   Follower still has old email (alice@old.com) ❌
          User sees stale data!
T=100ms:  Replication complete, Follower has new email ✓
```

---

## Consistency Tradeoffs

### Option 1: Strong Consistency (Read from Leader Only)

```
Guarantee: Always see latest data ✓
Downside: Can't scale reads (bottleneck at Leader)
Use when: Sensitive data (password, balance, payment)
```

### Option 2: Eventual Consistency (Read from Followers)

```
Guarantee: See data eventually (100ms-1s lag)
Benefit: Scale reads across followers ✓
Use when: Non-sensitive data (posts, recommendations)
Downside: Might see stale data briefly
```

---

## Real-World Pattern: Route by Sensitivity

**Don't route ALL reads the same way. Choose based on data sensitivity:**

### Sensitive Data (Read from Leader):
- Account balance
- Payments & transactions
- Password & authentication
- 2FA settings
- Email address
- Credit card info
- Account status (active/suspended)

**Reason:** Data loss or stale reads = catastrophic

### Non-Sensitive Data (Read from Followers):

- Public posts
- Recommendations
- Comments & likes
- Friend lists
- User profiles (non-financial)
- Notifications
- Analytics & reports

**Reason:** Stale reads acceptable, speed matters more

---

## Asynchronous vs Synchronous Replication

### Asynchronous (Most Common)

```
T=0ms:  Leader writes data
T=1ms:  Leader returns "Success" to app
T=5ms:  Starts sending to Followers
T=100ms: Followers receive it

Pros: ✓ Fast writes (1ms response)
Cons: ❌ Risk of data loss if Leader crashes before Followers replicate
```

### Synchronous

```
T=0ms:  Leader writes data
T=5ms:  Leader sends to Followers
T=10ms: Followers confirm received
T=11ms: Leader returns "Success" to app

Pros: ✓ Zero data loss (confirmed before responding)
Cons: ❌ Slow writes (10ms per write)
```

**Choice:** By sensitivity
- **Banking/Payments:** Sync (data loss unacceptable)
- **Notifications:** Async (speed matters, data loss acceptable)

---

## Leader Failure & Failover

### What Happens When Leader Crashes

```
Before: Leader (accepting writes)
        ↓ replicates
        Follower 1 (200ms behind)
        Follower 2 (500ms behind)

Leader crashes 💥
        
After:  Follower 1 → promoted to new Leader
        Follower 2 → new read-only Follower
```

### Failover Process

1. **Detect failure:** Health check times out
2. **Choose best Follower:** Pick the one most caught up (smallest replication lag)
3. **Promote:** Make it the new Leader
4. **Redirect traffic:** Point writes to new Leader
5. **Downtime:** Usually 30-60 seconds

### Data Safety During Failover

**Critical:** Promote the Follower with the MOST data (smallest lag)

```
Example:
T=100ms: Transaction written to Leader
T=300ms: Leader crashes
T=200ms: Follower 1 received it (safe if promoted)
T=500ms: Follower 2 would receive it (but too late)

If promote Follower 1 → transaction is safe ✓
If promote Follower 2 → transaction is lost ❌
```

---

## Real-World Patterns

### Pattern 1: Scale Reads for Analytics

```
Leader DB:
  • Regular app writes (user updates)
  • ~500 writes/sec

Follower (Analytics):
  • Heavy aggregation queries
  • "Top 1000 products by sales"
  • Doesn't slow down Leader ✓
```

### Pattern 2: Geographic Distribution

```
Leader (US-East):
  • All writes
  
Follower (EU):
  • Read-only replica
  • Low latency for EU users
  • Compliance: EU data stays in EU ✓
  
Follower (APAC):
  • Read-only replica
  • Low latency for Asia users
```

### Pattern 3: Backup & Disaster Recovery

```
Leader (prod):
  • Live writes

Follower (replica):
  • Sync copy for failover
  • If Leader fails → promote
  
Follower (backup):
  • Hourly snapshots
  • For disaster recovery
  • Can tolerate lag
```

---

## Monitoring Replication Lag

**Metrics to track:**
- Replication lag per Follower (milliseconds)
- Message timestamp vs when Follower received it
- Network latency to each Follower
- Replication throughput (bytes/sec)

**Alerts:**
- If lag > 1 second → investigate
- If lag keeps growing → capacity issue
- If lag spikes → network problem

**Actions:**
- Scale Follower resources (CPU, network)
- Investigate network issues
- Degrade gracefully (stop sending sensitive reads to that Follower)

---

## Key Takeaway

> **Leader-Follower replication scales reads and provides redundancy, but introduces replication lag. Route sensitive data to Leader (strong consistency), non-sensitive data to Followers (eventual consistency). Use synchronous replication for critical data (payments), asynchronous for speed (notifications). On Leader failure, promote the most-caught-up Follower (~30-60s downtime). Monitor replication lag constantly.**

---

## Questions Learned Today

1. ✅ Leader-Follower basics (where writes/reads go)
2. ✅ Replication lag and stale reads
3. ✅ Sensitivity-based routing (key pattern!)
4. ✅ Failover scenarios and data loss risks
5. ✅ Choosing async vs sync replication by sensitivity

---

## Next Session (Day 20)

**Topic:** Designing a URL Shortener (Case Study)  
**Preview:** Apply all 19 days of learning to design a real system. Database sharding strategy, replication, caching, consistency levels, traffic estimation.
