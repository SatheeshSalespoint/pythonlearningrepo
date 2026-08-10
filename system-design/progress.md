# 🏗️ System Design — Morning Learning Track

**Engineer:** Senior C# Backend Developer (12+ years)  
**Format:** 15 minutes every morning  
**Goal:** Master system design for scalable, real-world architectures  
**Start Date:** 2026-07-08  

---

## Progress Tracker

| Day | Topic | Status | Date | Key Takeaway |
|-----|-------|--------|------|--------------|
| Day 1 | Scalability — Vertical vs Horizontal | ✅ Done | 2026-07-08 | Design stateless from day 1 — never store sessions in server memory |
| Day 2 | Load Balancers | ✅ Done | 2026-07-09 | Health checks must verify real deps; sticky sessions = hidden single point of failure |
| Day 3 | Caching | ✅ Done | 2026-07-15 | Cache is a performance optimisation, not a data store — always invalidate on write, use Redis when horizontally scaled |
| Day 4 | Databases — SQL vs NoSQL | ✅ Done | 2026-07-16 | Start with SQL; NoSQL for scale/flexibility; most real systems use both |
| Day 5 | CAP Theorem | ✅ Done | 2026-07-17 | P is unavoidable — pick CP for correctness (payments/booking), AP for resilience (feeds/discovery); tune per operation |
| Day 6 | API Design — REST vs gRPC vs GraphQL | ✅ Done | 2026-07-20 | REST for public/CDN, gRPC for internal microservices, GraphQL BFF for flexible frontends; watch N+1 with DataLoader |
| Day 7 | Message Queues & Async Communication | ✅ Done | 2026-07-21 | Message queues trade latency for resilience; Channel\<T\> for in-process, Kafka for replay/audit, RabbitMQ/MassTransit for task dispatch; always define a DLQ strategy |
| Day 8 | Rate Limiting | ✅ Done | 2026-07-22 | Rate limit = hard reject (429); Throttle = soft slowdown; Circuit Breaker = fail fast outbound. Always use Redis for distributed counters; design keys per tenant/user/endpoint; define a Redis failure strategy |
| Day 9 | CDN & Static Assets | ✅ Done | 2026-07-24 | CDN caches at edge nodes globally — first request is always a MISS, every request after is a HIT; use content-hashed filenames for cache busting; Cache-Control: public for static, private/no-store for user data |
| Day 10 | Database Indexing & Query Optimisation | ✅ Done | 2026-07-28 | Index high-cardinality filter/sort columns; composite indexes follow left-prefix rule; avoid functions on indexed columns; use cursor pagination (not OFFSET) and read replicas at scale |
| Day 11 | Microservices vs Monolith | ✅ Done | 2026-07-29 | Start with a modular monolith; microservices solve team/deployment boundaries — shared DB + microservices = distributed monolith (worst of both worlds) |
| Day 12 | Service Discovery | ✅ Done | 2026-07-30 | Service registry = phone book for microservices; K8s DNS+Services is built-in discovery; always back registry with real health checks |
| Day 13 | Circuit Breaker Pattern | ✅ Done | 2026-07-31 | CB = fail fast in 3 states (Closed→Open→Half-Open); combines with Retry (transient) + Fallback (degradation); never retry when circuit is open — use Polly in .NET |
| Day 14 | Event-Driven Architecture | ✅ Done | 2026-08-03 | Producers emit past-tense facts; consumers must be idempotent; partition by entity ID for ordering; keep payment charges synchronous — publish events only after critical action succeeds |
| Day 15 | CQRS Pattern | ✅ Done | 2026-08-04 | Commands return only server-generated data (usually just the ID); queries can use joins — CQRS forbids domain logic in queries, not SQL joins; scale read side with replicas not over-engineering |
| Day 16 | Event Sourcing | ✅ Done | 2026-08-06 | Event store = append-only facts per aggregate; use aggregate_type not separate tables; build projections for reports, snapshots for replay performance, archive for cost — never query event store directly for reporting |
| Day 17 | Consistent Hashing | ✅ Done | 2026-08-07 | Consistent hashing rehashes only ~1/N of keys when scaling (vs 67% with simple hashing); use for cache/queue/DB routing; sub-partition skewed tenants to prevent hot spots |
| Day 18 | Database Sharding | ✅ Done | 2026-08-10 | Shard key selection (high cardinality, immutable, evenly distributed); data skew ≠ traffic skew; tradeoffs: joins slow, distributed transactions risky, hot shards possible; use consistent hashing for rebalancing; fix data skew with sub-sharding, traffic skew with caching/replicas |
| Day 19 | Replication — Leader/Follower | ✅ Done | 2026-08-11 | Leader accepts writes, Followers scale reads; replication lag (100ms-1s) causes stale reads; route sensitive data to Leader (strong consistency), non-sensitive to Followers (eventual consistency); sync for payments, async for speed; failover promotes most-caught-up Follower (~30-60s downtime) |
| Day 20 | Designing a URL Shortener (case study) | ⬜ | | |

---

**Status Legend:** ⬜ Not Started &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ✅ Done
