# Day 27: Metrics & Monitoring System

**Date:** 2026-08-26  
**Status:** ✅ Done  
**Confidence:** 8/10 (solid design, practical understanding)  
**Communication Level:** 8/10 → 8.5/10 ✅ (Phase 1 complete!)

---

## System Overview

**What:** Metrics collection and monitoring system for multi-tenant fintech SaaS  
**Context:** SalesPoint (payments, invoices, authentication, analytics)  
**Scale:**
- 100K tenants
- 50K req/sec peak
- 30-day retention (hot) + 1-year archive (cold)
- Multi-region (NZ, AUS)

**Core Problem:** Collect millions of metrics efficiently without cardinality explosion, while maintaining real-time monitoring and historical analysis capability.

---

## Bottleneck Identified

### Primary Bottleneck: Cardinality Explosion

**The Problem:**
```
Naive approach: Track all dimensions
  payment_latency{tenant_id, endpoint, status, region, currency}
  = 100K × 50 × 3 × 2 × 3 = 9 billion combinations!
  
Result:
  • Prometheus memory: Can't fit indices (500GB+ needed)
  • Disk storage: Terabytes (unaffordable)
  • Query latency: Minutes (unusable)
  • System crashes ❌
```

**Root Cause:** Including high-cardinality dimensions (tenant_id, user_id) in metric labels

**Solution:** Selective labeling + Sampling strategy

---

## Design Decisions

### Decision 1: Retention & Storage

```
Prometheus (Hot Storage):
  • Retention: 30 days
  • Storage: ~70GB (low cardinality labels)
  • Memory: ~2GB (indices + recent data)
  • Query latency: <5 seconds
  
Data Warehouse (Cold Storage):
  • Retention: 1 year
  • Storage: ~50GB (compressed daily aggregates)
  • Cost: ~$50/month (S3 + query)
  • Query latency: Minutes (batch queries ok)
```

---

### Decision 2: Query Latency

```
Prometheus (Real-time):
  • Latency: < 5 minutes (acceptable for operational dashboards)
  • Use case: Real-time alerts, operational dashboards
  • Metrics: Current payment latency, error rates, cache hit ratios
  
Data Warehouse (Historical):
  • Latency: Hours to minutes (batch queries)
  • Use case: Trending, compliance, business analysis
  • Metrics: Revenue trends, churn analysis, cost per transaction
```

**Reasoning:** Metrics show what happened (not instant decisions), so 5-minute delay is acceptable for most dashboards.

---

### Decision 3: Sampling Strategy

**Three-tier sampling approach:**

```
TIER 1: CRITICAL (100% sampling)
  Endpoints: POST /api/payments, POST /api/invoices, POST /api/refunds
  Reason: Money-critical, must track every transaction
  Result: 25K metrics/sec (100% of critical traffic)
  
TIER 2: IMPORTANT (10% sampling)
  Endpoints: Auth, balance queries, account updates
  Reason: Important but failures are obvious
  Example: 20K req/sec × 10% = 2K metrics/sec
  Storage savings: 10x reduction
  
TIER 3: NON-CRITICAL (1% sampling)
  Endpoints: Profile, categories, settings (read-only)
  Reason: Non-business-critical, trends only
  Example: 5K req/sec × 1% = 50 metrics/sec
  Storage savings: 100x reduction

Total metrics/sec:
  25K (critical) + 2K (important) + 50 (non-critical) = ~27K/sec
  vs. 50K/sec without sampling = 46% reduction
```

**Why sampling works:**
```
Without sampling: Every request tracked
  • 50,000 data points/sec
  • Storage: 100GB/month
  
With 10% sampling: 1 in 10 tracked
  • 5,000 data points/sec
  • Storage: 10GB/month (10x cheaper!)
  
Quality: Still see patterns clearly
  • Avg latency detectable
  • Anomalies visible
  • Problems caught quickly
```

---

### Decision 4: Label Strategy (Low Cardinality)

```
❌ WRONG (High cardinality):
  payment_latency{tenant_id, user_id, endpoint, status}
  = 100K × 1M × 50 × 3 = 15 trillion combinations!

✅ RIGHT (Low cardinality):
  payment_latency{endpoint, status, region}
  = 50 × 3 × 2 = 300 combinations
  
Cardinality reduction: 50 billion:1
Memory saved: Indices fit in 100MB (not 500GB)
```

**Why not track tenant_id?**
- Metrics are for SERVICE HEALTH, not per-tenant debugging
- Per-tenant issues → use LOGS, not metrics
- Metrics should aggregate across tenants

---

### Decision 5: Architecture Split

```
PROMETHEUS (Real-Time Operations):
  • For: Ops team, real-time dashboards, alerting
  • Stores: Last 30 days of detailed metrics
  • Queries: <5 second latency
  • Metrics: Payment latency, error rate, cache hit ratio
  
DATA WAREHOUSE (Historical Analysis):
  • For: Business team, compliance, analytics
  • Stores: 1 year of daily aggregates
  • Queries: Minutes (batch jobs ok)
  • Metrics: Revenue trends, churn analysis, cost/transaction
```

---

## Complete System Architecture

### Layer 1: Collection (Application Level)

```csharp
// Critical endpoints (100% sampling)
metrics.RecordLatency("payment.latency", duration);
metrics.Increment("payment.success");
metrics.Increment("payment.failure");

// Important endpoints (10% sampling)
if (Random(0, 10) == 0) {
  metrics.RecordLatency("balance.latency", duration);
}

// Non-critical endpoints (1% sampling)
if (Random(0, 100) == 0) {
  metrics.RecordLatency("profile.latency", duration);
}

// All metrics exposed via /metrics endpoint
GET http://localhost:8080/metrics
  ├─ payment_latency_p99: 245ms
  ├─ payment_success_total: 1,234,567
  ├─ cache_hit_ratio: 0.94
  └─ error_rate: 0.02%
```

---

### Layer 2: Prometheus (Real-Time Storage)

```
Configuration:
  • Scrape interval: 15 seconds
  • Retention: 30 days
  • Memory: ~2GB (indices + hot data)
  • Disk: ~70GB (TSDB compressed format)

Data Flow:
  Application (/metrics endpoint)
    ↓ (every 15 sec)
  Prometheus scrapes
    ↓
  In-memory indices + recent data (hot)
    ↓ (older than 1 hour)
  Disk storage (TSDB format)
    ↓ (older than 30 days)
  Archive to Data Warehouse
```

---

### Layer 3: Alerting Rules

```
Rule 1: Payment Latency High
  IF payment_latency_p99 > 500ms FOR 5 minutes
  THEN alert "Payment processing slow" → Slack/PagerDuty

Rule 2: Payment Failure Rate High
  IF payment_success_rate < 99.5% FOR 2 minutes
  THEN alert "Payment failures detected" → PagerDuty

Rule 3: Cache Performance Degrading
  IF cache_hit_ratio < 85% FOR 10 minutes
  THEN alert "Cache efficiency low" → Slack
```

---

### Layer 4: Data Warehouse (Historical Storage)

```
Daily Batch Job (Midnight):
  1. Export Prometheus last 24 hours
  2. Aggregate by hour
  3. Load into BigQuery/Snowflake
  4. Archive old Prometheus data to S3
  5. Keep 30-day rolling window in Prometheus

Storage:
  • Daily aggregates: ~1GB/day
  • 1 year: ~365GB (compressed to ~50GB)
  • Cost: ~$50/month (S3 + query fees)

Available Queries:
  • Revenue trend (6 months)
  • Payment success rate trend
  • Customer churn analysis
  • Cost per transaction
```

---

### Layer 5: Visualization

```
PROMETHEUS + GRAFANA (Real-time):
  Dashboard 1: Payment Health
    ├─ Payment latency (live, p99)
    ├─ Success rate (live, %)
    ├─ Failure count (live)
    └─ Retry rate (live)
  
  Dashboard 2: System Health
    ├─ Error rate (live)
    ├─ Cache hit ratio (live)
    ├─ DB connection pool (live)
    └─ CPU/Memory usage (live)
  
  Users: Ops team, on-call engineers

DATA WAREHOUSE REPORTS:
  Report 1: Revenue Dashboard
    ├─ Daily revenue (last 6 months)
    ├─ Payment method breakdown
    └─ Conversion rate trend
  
  Report 2: Compliance Report
    ├─ Payment settlement times (daily)
    ├─ Audit trail completeness
    └─ SLA uptime (monthly)
  
  Users: Business team, compliance team
```

---

## Storage & Cost Calculation

```
PROMETHEUS (30-day hot storage):
  Critical metrics: 25K/sec × 86,400s × 30 days = 64.8 billion points
  Compression: ~1 byte/point
  
  Storage breakdown:
    • Critical: ~65GB
    • Important: ~6.5GB
    • Non-critical: ~0.1GB
    ────────────────
    • Total: ~70GB
  
  Cost: ~$10/month (on-premise) or ~$50/month (cloud)

DATA WAREHOUSE (1-year cold storage):
  Daily aggregates: 365 days × 1GB/day = 365GB
  Compressed: ~50GB (7:1 ratio)
  
  Cost: ~$50/month (S3 + BigQuery queries)

TOTAL MONTHLY COST: ~$100 (manageable for fintech)
```

---

## Bottleneck Solutions Summary

| Bottleneck | Root Cause | Solution |
|-----------|-----------|----------|
| **Cardinality explosion** | High-cardinality labels (tenant_id) | Low-cardinality labels (endpoint, status, region only) |
| **Storage explosion** | Tracking 100% of requests | Sampling (10-100% by criticality) |
| **Memory exhaustion** | Prometheus indices huge | Remove unnecessary labels, compress indices |
| **Query latency** | Too many time-series to search | Reduced cardinality = faster queries |
| **Long-term storage** | Prometheus retention too long | Archive to Data Warehouse, keep 30 days in Prometheus |
| **Per-tenant issues** | Metrics mixed with logs | Separate concerns: metrics for service health, logs for debugging |

---

## Key Learnings

### Domain-Specific Design
✓ Fintech needs: Real-time alerts (payments) + Historical analysis (compliance)  
✓ Not all data needs same retention or latency  
✓ Different data types → Different storage strategies  

### Cardinality Thinking
✓ High-cardinality dimensions explode exponentially  
✓ Tenant_id, user_id, request_id = death by a thousand cuts  
✓ Track service health, not individual user metrics  

### Sampling as Efficiency Tool
✓ 10% sampling catches 90% of issues  
✓ Sampling by criticality = best of both worlds  
✓ 100% of critical data, 10% of medium, 1% of non-critical  

### Architecture Separation
✓ Prometheus: Real-time operations (alerts, dashboards)  
✓ Data Warehouse: Historical analysis (trends, compliance)  
✓ Different tools for different purposes  

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Bottleneck identification** | 9/10 — Cardinality explosion is primary |
| **Sampling strategy** | 8/10 — Understood trade-offs |
| **Label design** | 9/10 — Low cardinality clear |
| **Architecture split** | 8/10 — Prometheus vs DW purpose |
| **Storage calculations** | 8/10 — Numbers make sense |
| **Alerting strategy** | 7/10 — Basic rules understood |

**Overall Day 27:** 8/10 ✅

---

## Communication Progress

### Phase 1 Complete (Days 25-27)

| Metric | Day 25 | Day 26 | Day 27 |
|--------|--------|--------|--------|
| **Communication** | 7/10 | 8/10 | 8.5/10 ✅ |
| **Structure** | Improving | Excellent | Excellent |
| **Confidence** | Better | Strong | Very Strong |
| **Self-awareness** | Emerging | Strong | Mastery |

### What Improved in Day 27
- ✓ **Asked clarifying questions** ("What is sampling?") instead of guessing
- ✓ **Learned the framework** (constraint → design → tradeoff)
- ✓ **Applied concepts independently** (identified critical vs non-critical endpoints)
- ✓ **Explained reasoning clearly** (why 100% vs 10% vs 1% sampling)
- ✓ **Owned the design decisions** (not just accepting, but validating)

### Communication Target: ACHIEVED ✅

**Goal was:** 6.5/10 (Day 24) → 8.5/10 (end of Day 27)  
**Actual:** 6.5 → 7 → 8 → 8.5 ✅

You've reached **senior-level communication** through Days 25-27:
- Clear problem identification
- Confident language ("I recommend X because Y")
- Structured answers (constraint → tradeoff → decision)
- Willingness to ask clarifying questions
- Self-correction and refinement

---

## Phase 1 Summary (Days 22-27)

| Day | System | Confidence | Communication |
|-----|--------|-----------|-----------------|
| Day 22 | Analytics URL Shortener | 6/10 | 6/10 |
| Day 23 | Instagram Feed | 8/10 | 6/10 |
| Day 24 | Google Autocomplete | 9/10 | 6.5/10 |
| **Day 25** | **Rate Limiting** | **7/10** | **7/10** (+0.5) |
| **Day 26** | **Cache Invalidation** | **8/10** | **8/10** (+1.0) |
| **Day 27** | **Metrics & Monitoring** | **8/10** | **8.5/10** (+0.5) |

**Total Growth:**
- Technical: 6/10 → 8/10 (+2 points, plateau at expert level)
- Communication: 6.5/10 → 8.5/10 (+2 points, now at senior engineer level)

---

## Checkpoint Assessment (Day 35 Readiness)

**Phase 1 Complete ✅**
- ✓ Scale estimation accuracy (confident on 50K req/sec calculations)
- ✓ Bottleneck identification (consistency vs performance vs cardinality)
- ✓ Architectural questioning (asking WHY, not just WHAT)
- ✓ Tradeoff analysis (cost vs accuracy, latency vs consistency)
- ✓ Multiple constraints simultaneously (fintech + scale + compliance)
- ✓ Real-time systems + eventual consistency understanding (Days 23-24)

**Ready for Phase 2 (Medium Difficulty)?** 
- YES ✅ Technical foundation strong, communication polished

**Days 28-35 Preview:**
- Day 28: Twitter/Social Media Feed (fanout patterns advanced)
- Day 29: Messaging Queue (reliability, ordering, deduplication)
- Day 30: Notification System (reliability, fan-out, deduplication)
- Days 31-35: Key-Value Store, Session Store, Search Engine, Leaderboard, Recommendation Engine

**Your next checkpoint:** Day 35 (mid-Phase 2) — Reassess readiness for Phase 3 (Hard systems)

---

**Status:** ✅ Phase 1 Complete — Ready for Phase 2  
**Brain State:** 🧠 Excellent progress, momentum building  
**Next:** Day 28 — Twitter/Social Media Feed (advanced fanout)  
**Communication Target:** Maintain 8.5/10, push toward 9/10 in Phase 2
