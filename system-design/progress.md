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
| Day 20 | Designing a URL Shortener (case study) | ✅ Done | 2026-08-12 | Shard by short_url (reads > writes); user_id + sequence for collision-free generation; Redis cache + read replicas for scale; separate analytics DB for secondary queries; cache lock prevents stampede on viral URLs |
| Day 21 | Authentication System Design (Real App) | ✅ Done | 2026-08-13 | Multi-tenant SaaS+Fintech auth: JWT + refresh tokens; regional Redis sharding (NZ/AUS); IP+user rate limiting; audit logging (Seq+CosmosDB); 5-min Redis failure fallback; security-first design for fintech compliance |
| Day 22 | Analytics-Heavy URL Shortener | ✅ Done | 2026-08-14 | Daily batch aggregation (not hourly); time-based partitioning (monthly rotation); eventual consistency (24-hour delay acceptable); index strategy (link_id, date); no bottleneck with proper design; confidence 6/10 |
| Day 23 | Instagram Feed (Social Media Timeline) | ✅ Done | 2026-08-15 | Hybrid fanout (write for <100K followers, read for celebs); Redis + SQL hybrid storage; differential consistency (strong for creator, eventual for followers); no bottleneck with proper caching; confidence 8-9/10 |
| Day 24 | Google Search Autocomplete | ✅ Done | 2026-08-19 | Trie data structure for prefix matching; balanced ranking (long-term × 1.0 + short-term × 1.0); hybrid 3-tier storage (Trie 1M hot + Redis warm + DB cold); reserved capacity 900K+100K tiers; daily batch promotion logic; confidence 9-10/10 |
| Day 25 | Rate Limiting Service | ✅ Done | 2026-08-20 | Regional sharding (NZ/AUS split); tenant-based consistent hashing; sub-sharding for hot tenants (>1K req/sec); primary-only consistency (no replica reads); TTL-based memory management; confidence 7/10 |
| Day 26 | Cache Invalidation System | ✅ Done | 2026-08-21 | Staleness tolerance per data type (transaction 1s, balance 5s, history 5s); hybrid invalidation (event + TTL); scoped events (not broadcast); outbox pattern for guaranteed delivery; confidence 8/10 |
| Day 27 | Metrics & Monitoring System | ✅ Done | 2026-08-26 | Cardinality explosion bottleneck; three-tier sampling (100%/10%/1%); low-cardinality labels (endpoint, status, region only); Prometheus real-time + Data Warehouse historical; confidence 8/10 |
| Day 28 | Twitter/Social Media Feed | ✅ Done | 2026-08-26 | Pull-on-demand architecture; fanout bottleneck solved; hybrid regional replication (5min posts, 1hr likes); engagement aggregation strategy; confidence 8/10 |
| Day 29 | Messaging Queue System | ✅ Done | 2026-08-28 | Manual ACK for reliability; idempotency keys (hybrid Redis+DB); tenant-based partitioning (10 queues); sequence gap handling (skip & alert); confidence 8.5/10 |
| Day 30 | Notification System (Multi-Channel) | ✅ Done | 2026-08-31 | 3 independent services (email/SMS/push); hybrid channel strategy (critical=all, non-critical=email); retry 28x over 24hrs; DLQ with ops alerting; confidence 8.5/10 |
| Day 31 | Notification System Refined | ✅ Done | 2026-09-01 | Idempotency hybrid (Redis+DB); priority-based batching (Rank1→3, 10 msg/batch); regional failover (health check + circuit breaker); database disaster recovery (3-layer backup); index optimization (left-prefix rule); confidence 9/10 |

---

## Learning Strategy & Checkpoints

**Commitment:** Daily system design practice (30+ days minimum)

**Approach:** 
- Days 22-35: Complete Phase 1 (EASY) + Phase 2 (MEDIUM)
- End of Day 35: Assessment checkpoint
- Decision point: Ready for Phase 3 (HARD systems)?
  - If YES → Proceed with hard systems (Days 36-45)
  - If NO → Adjust plan (add question-building, slow down, etc.)

**Assessment Criteria (End of Day 35):**
✓ Can estimate scale correctly (traffic, storage, QPS)  
✓ Identify bottlenecks immediately  
✓ Ask good architectural questions (not just answer them)  
✓ Understand consistency/availability tradeoffs deeply  
✓ Handle multiple constraints simultaneously  
✓ Ready for real-time systems + strong consistency  

---

## 60+ Day Learning Roadmap (Comprehensive Daily Practice)

### Phase 1: EASY (Days 22-27) — 15-20 mins each
**Goal:** Build confidence with cache + basic scaling patterns

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 22 | **URL Shortener Variants** (TinyURL vs Bit.ly patterns) | Easy | Query optimization, different sharding strategies | 15 min |
| Day 23 | **Instagram Feed** (simpler than Twitter) | Easy | Basic caching, timeline ordering | 20 min |
| Day 24 | **Google Search Autocomplete** | Easy | Trie data structure, prefix matching, caching | 20 min |
| Day 25 | **Rate Limiting Service** | Easy | Token bucket, sliding window, distributed counters | 15 min |
| Day 26 | **Cache Invalidation System** | Easy | TTL strategies, cache warming, consistency | 20 min |
| Day 27 | **Metrics/Monitoring System** | Easy | Time-series DB, aggregation, alerts | 20 min |

### Phase 2: MEDIUM (Days 28-35) — 30-45 mins each
**Goal:** Handle tradeoffs, consistency models, distributed systems

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 28 | **Twitter/Social Media Feed** | Medium | Fanout-on-write, denormalization, eventual consistency | 45 min |
| Day 29 | **Messaging Queue (RabbitMQ style)** | Medium | Producer-consumer, ordering, reliability | 40 min |
| Day 30 | **Notification System** | Medium | Reliability, fan-out, deduplication | 35 min |
| Day 31 | **Key-Value Store (Redis style)** | Medium | Eviction policies, persistence, pub/sub | 40 min |
| Day 32 | **Session Store** (similar to auth but simpler) | Medium | Distributed sessions, expiration, cleanup | 30 min |
| Day 33 | **Search Engine (basic)** | Medium | Indexing, ranking, inverted index | 45 min |
| Day 34 | **Leaderboard/Rankings System** | Medium | Sorted sets, real-time updates, scalability | 35 min |
| Day 35 | **Recommendation Engine (basic)** | Medium | Collaborative filtering, caching, batch jobs | 40 min |

### Phase 3: HARD (Days 36-45) — 45-60 mins each
**Goal:** Master complex tradeoffs, real-time systems, strong consistency

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 36 | **Uber (Ride Sharing)** | Hard | Geolocation, real-time matching, strong consistency | 60 min |
| Day 37 | **YouTube (Video Streaming)** | Hard | Storage, CDN, transcoding, distributed encoding | 60 min |
| Day 38 | **Google Maps** | Hard | Geospatial indexing, routing, real-time traffic | 55 min |
| Day 39 | **Slack (Workspace Platform)** | Hard | Real-time messaging, presence, search | 60 min |
| Day 40 | **Stripe (Payment System)** | Hard | Strong consistency, reliability, compliance, idempotency | 60 min |
| Day 41 | **Discord (Real-time Chat)** | Hard | Message ordering, consistency, reliability, presence | 60 min |
| Day 42 | **Netflix (Video Service)** | Hard | Recommendation, streaming, CDN, global distribution | 60 min |
| Day 43 | **Amazon S3 (Object Storage)** | Hard | Distributed storage, replication, consistency | 55 min |
| Day 44 | **GitHub (Code Collaboration)** | Hard | Version control, branching, conflict resolution | 60 min |
| Day 45 | **Kafka (Event Streaming)** | Hard | Partitioning, ordering, replication, fault tolerance | 60 min |

### Phase 4: VERY HARD (Days 46-55) — 60+ mins each
**Goal:** Design complex, multi-faceted distributed systems

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 46 | **Google Drive (Cloud Storage + Sync)** | Very Hard | Sync protocols, conflict resolution, eventual consistency | 70 min |
| Day 47 | **Airbnb (Marketplace)** | Very Hard | Search, inventory, transactions, trust, payments | 75 min |
| Day 48 | **DynamoDB (NoSQL Database)** | Very Hard | Distributed hash table, replication, auto-scaling | 70 min |
| Day 49 | **Cassandra (Distributed DB)** | Very Hard | Ring topology, eventual consistency, read repair | 75 min |
| Day 50 | **Facebook (Social Network)** | Very Hard | Graph DB, privacy, real-time notifications | 75 min |
| Day 51 | **LinkedIn (Connections + Feed)** | Very Hard | Graph algorithms, feed ranking, job recommendations | 70 min |
| Day 52 | **Evernote (Note Taking + Sync)** | Very Hard | Rich content, encryption, offline-first, sync | 70 min |
| Day 53 | **Dropbox (File Sync Service)** | Very Hard | Delta sync, versioning, conflict resolution | 75 min |
| Day 54 | **Docker Registry (Container Storage)** | Very Hard | Distributed image storage, layering, replication | 70 min |
| Day 55 | **AWS Lambda (Serverless)** | Very Hard | Scheduling, scaling, cold starts, isolation | 75 min |

### Phase 5: YOUR REAL APP (Days 56-65) — Custom duration
**Goal:** Design critical systems for your SaaS+Fintech platform

| Day | System | Your Pain Point | Focus | Approx Time |
|-----|--------|------------------|-------|------------|
| Day 56 | **Reporting System** | Reports hanging | Async processing, materialized views, caching | 45 min |
| Day 57 | **Data Pipeline (ETL)** | Real-time analytics | Streaming, batching, incremental updates | 50 min |
| Day 58 | **User Onboarding Flow** | Conversion optimization | Multi-step, validation, emails, notifications | 40 min |
| Day 59 | **Payment Processing** | Fintech core | Transactions, retries, idempotency, audit | 60 min |
| Day 60 | **Search/Autocomplete** | User experience | Indexing, ranking, real-time suggestions | 45 min |
| Day 61 | **Audit Logging (Enhanced)** | Compliance | Tamper-proof logs, compliance reporting | 40 min |
| Day 62 | **Analytics Dashboard** | Business intelligence | Real-time metrics, aggregations, visualizations | 50 min |
| Day 63 | **Multi-region Replication** | Global expansion | Data consistency, conflict resolution | 55 min |
| Day 64 | **Disaster Recovery System** | Business continuity | Backup, restore, failover, testing | 50 min |
| Day 65 | **Migration from Legacy** | Technical debt | .NET Framework → .NET 8, session → JWT | 60 min |

### Phase 6: ADVANCED TOPICS (Days 66+) — Optional deep dives
**Goal:** Specialize in specific areas

**Distributed Systems Theory:**
- CAP Theorem deep dive
- ACID vs BASE
- Consensus algorithms (Raft, Paxos)
- Byzantine fault tolerance

**Performance Optimization:**
- Query optimization techniques
- Index strategies
- Caching patterns (LRU, LFU, TTL)
- Bloom filters & sketches

**Data Structures at Scale:**
- B-trees & LSM trees
- Merkle trees
- Tries & suffix trees
- Skip lists

**Security & Compliance:**
- End-to-end encryption
- Key management
- Zero-knowledge proofs
- GDPR/compliance patterns

---

## Practice Guidelines

### Daily Routine (Suggested)
```
Monday-Friday: ~30-45 mins
  • Pick system from roadmap
  • Apply 5-question framework
  • Design on paper or whiteboard
  • Document key decisions
  
Weekend: Review + Deeper dive (optional)
  • Pick one system from week
  • Implement part of it (code)
  • Read real-world case studies
```

### Success Metrics
```
✓ Can estimate scale correctly
✓ Ask good architectural questions
✓ Identify bottlenecks immediately
✓ Propose multiple solutions + tradeoffs
✓ Explain why you chose your approach
✓ Handle failure scenarios
✓ Think about costs + operational concerns
```

### Progression
```
Week 1-2 (Days 22-27): Build confidence with easy systems
Week 3-4 (Days 28-35): Medium systems, start asking own questions
Week 5-7 (Days 36-45): Hard systems, deep tradeoff analysis
Week 8-10 (Days 46-55): Very hard systems, multi-dimensional thinking
Week 11-13 (Days 56-65): Your real app systems, practical application
Week 14+: Advanced topics or specialized deep dives
```

---

**Status Legend:** ⬜ Not Started &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ✅ Done
