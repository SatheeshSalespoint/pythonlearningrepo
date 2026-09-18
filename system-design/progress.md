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
| Day 32 | Redis-Style KV Store | ✅ Done | 2026-09-02 | RDB + AOF persistence (fast recovery + zero loss); LFU eviction with critical data protection; tiered DB sync (1-min critical, 5-min non-critical); bottleneck-first architecture; confidence 8.5/10 |
| Day 33 | Search Engine (Basic) | ✅ Closed on Day 37 | 2026-09-03 | Inverted index (word → doc list, intersect for query); autocomplete ≠ search engine (trie vs inverted index); doc length belongs in ranking not indexing; scale corrected 100M records / 50GB index / ~1.4K peak QPS; **resume: Q2 constraint, Q3 freshness, Q4 tenant isolation, ranking, sharding**; confidence 5/10 |
| Day 34 | Leaderboard / Rankings System | ✅ Done | 2026-09-04 | Sorted sets maintain order on WRITE so reads just navigate; skip list + hash dual structure, spans make ZREVRANK O(log N) not O(1); ~100 bytes/member, listpack under 128; dimension explosion 100K × 4 windows × 3 metrics = 1.2M boards ≈ 24GB; **WRITE-heavy 11:1 — inverts Days 20-33, caching useless here**; 5% vs 20% txn assumption flipped the architecture verdict; challenge unsourced numbers, measure with redis-benchmark; confidence 8/10 |
| Day 35 | **Checkpoint Assessment (Days 22-34)** | ✅ Done | 2026-09-08 | **Score 6.0/10 — NOT ready for Phase 3.** Passed: scale estimation (7.5). Partial: bottleneck ID (6.5), asking questions (7.0). **Failed: consistency tradeoffs (5.0) — conflated consistency with availability, proposed multi-leader as a consistency fix, stated no costs; multi-constraint (4.0) — handled serially not simultaneously.** Key gaps: consistency is a property of the reader↔write relationship, not of tables (read-your-own-writes vs monotonic reads); per-key reads-per-write decides precompute (>1) vs compute-on-read; batch-job bottleneck is the critical path + recovery story, not QPS; SLA is cheap because recency is 3.5% of retention. **Pattern: strong at quantifying what is given, weak at interrogating it.** Bridge phase Days 36-41 before Phase 3 reopens Day 42 |
| Day 36 | **Consistency Models (mechanism-first)** | ✅ Done | 2026-09-09 | Teaching day, checks 3/3. **Consistency = property of the reader↔write relationship, not of tables.** Four anomalies, all from *healthy* async replication (so failover fixes address none): own write vanishes → read-your-own-writes (sticky ~2s, or LSN/GTID tracking); time runs backwards → **monotonic reads (nearly free, covers non-writers — the overlooked one, and the Round 3(c) answer)**; effect before cause → consistent prefix (same partition or version vectors); observers disagree → linearizable (costs a round trip per write + availability under partition). Session guarantees are siblings, not a ladder. **Decision procedure: who is the observer → what anomaly would they notice → cheapest guarantee that prevents it.** Reach for linearizable when concurrent writers can corrupt state (double-spend), not when data feels important. Freshness ≠ consistency (batch job needs "caught up past midnight", no guarantee). ⚠️ Relapse: still sorted data into critical/non-critical on Q3 — re-test Day 39 |
| Day 37 | **Search Engine — Architecture Complete** (closes Day 33) | ✅ Done | 2026-09-10 | Q2 8/10, Q3 7.5/10, Q4 6/10. Confidence 5→7/10. **Headline: partitioning by TENANT instead of by document deleted the whole distributed architecture** — no fan-out, no coordinator, no merge, no tail latency; 8,000 tenants × 12,500 recs = ~6MB per tenant index, so the 50GB total never constrains a query. **Derived stores can't be fixed by routing** — replication lag is a copy behind, index lag is a structure not yet rebuilt; sticky sessions fix the first, never the second (applies to CQRS projections, materialised views, rollups). Freshness via dual index (main + live in RAM, ~60s) with immutable segments + background compaction — same pattern as Day 32 RDB+AOF and LSM trees. Physical isolation beats a WHERE clause when correctness is the currency at risk (filter bug = regulatory event). Business search ranks on **workflow state** (recency, unpaid, amount), not text — BM25 solves a problem a 12,500-record corpus doesn't have. Re-derived IDF unprompted; challenged an asserted cost correctly (new behaviour). ⚠️ Terms ≠ indexes, postings ≠ vocabulary; arithmetic failure moved from lost zeros to un-stepped units (KB→MB→GB). Session ran long — pacing note for Days 39-41 |
| Day 38 | **Applied Session — Xe Rate Alerts (production design)** | ✅ Done | 2026-09-16 | Not on the roadmap — scaled own take-home ([xe-hiring-takehome](../../Xe/xe-hiring-takehome-csharp-vue/xe-hiring-takehome)) to 10K users/50K alerts/200 pairs. **Self-corrected twice unprompted:** proposed per-user DB reads (10K queries/cycle), caught it as the same batching-gap mistake just found on the write side; mislabeled outbox→relay→broker as having the "dual-write problem" when it's the fix for it. Correctly separated evaluation (CPU, in-memory, cheap) from writes (DB, batchable) from notifications (blocking calls to a third party you don't control — the real bottleneck: total blocking work doesn't shrink just because you poll less often). Diagnosed direct-publish-to-broker as having both dual-write AND a silent-loss consistency hazard (DB says triggered, broker never got it) — good transfer of Day 36 consistency-anomaly thinking onto a write path. Landed **naming costs unprompted** across all three notification designs — the specific Day 35 gap. One relapse: asked "what breaks under load" (capacity), answered "what if DB goes down" (availability) — same conflation as Day 35 Round 3, corrected in-turn once named. Also overstated a guarantee ("delivered within 5 sec") with no mechanism backing the bound — corrected to at-least-once + idempotency key. **Day 39 consistency re-test still pending**, moved from today |
| Day 39 | **Consistency Re-Test** | ✅ Done | 2026-09-17 | **Score 8.2/10 — consistency gate CLEARED.** Round 3 re-run (merchant refund/follower lag) 8.5/10: named read-your-own-writes and monotonic reads unprompted, led with the cheap fix, stated costs unpushed, and explained leader overload in pure capacity terms without once reaching for "if it goes down" (the Day 38 tell). New scenario (delivery-status flicker) 7/10: correct diagnosis and guarantee immediately, but needed 3 prompts to see that a 2-second sticky window (borrowed from the write-then-read case) doesn't survive a 30-minute polling session — landed on log-position tracking once walked through the failure. New scenario (post/reply causal ordering) 9/10: named causal consistency, gave the exact same-partition mechanism from Day 36, and stated its real cost (fights load-distribution) — all cold, unprompted, no follow-up needed. **New finding:** doesn't yet stress-test his own proposed mechanism against the scenario's actual scale before presenting it. **Session feedback:** self-rated understanding jumped 5→8/10 from the cold-Q&A-with-follow-up-pressure format itself — confirmed this format is a teaching tool, not just assessment. **Requested more sessions like this before Phase 3** — specifically to build confidence stating "no bottleneck exists" plainly (same root cause as Day 35 Round 2: correct conclusion, abandoned under pressure). Bridge phase extended one day to add this drill |
| Day 40 | **Bottleneck-Confidence Drill** (new, requested Day 39) | ✅ Done | 2026-09-18 | **Score 7.0/10** — not a gate day, a confidence drill; the within-session trend is the real signal. Round 1 (5/10) reproduced the exact Day 35 Round 2 pattern live: computed correctly that a 5,000-merchant statement job had no bottleneck (3.47h in a 6h window), then abandoned that verdict FOUR times, each reaching for a hypothetical — once directly contradicting his own prior arithmetic while trying to sound reassuring. Arithmetic flawless throughout; purely a narrative-discipline gap. **Fix that worked:** forcing the answer into three physically separate sentences — verdict (unconditional) → headroom number → risk note (explicitly separate, conditional) — stopped the leakage immediately. Round 2 (8/10, clean inventory-reconciliation case, 48× headroom): unconditional verdict on the first try, AND held it under a direct leading push ("48× sounds too good, surely there's a bottleneck") — the exact moment that broke on Day 35. Round 3 (8/10, same job + a genuine burst-constraint bottleneck): confirmed no overcorrection — called a real bottleneck correctly and cleanly once one actually existed, then priced the async fix in the right currency (DB connection-pool pressure), not "no cost" |

---

## Learning Strategy & Checkpoints

**Commitment:** Daily system design practice (30+ days minimum)

**Approach:** 
- Days 22-35: Complete Phase 1 (EASY) + Phase 2 (MEDIUM)
- End of Day 35: Assessment checkpoint
- Decision point: Ready for Phase 3 (HARD systems)?
  - If YES → Proceed with hard systems (Days 36-46)
  - If NO → Adjust plan (add question-building, slow down, etc.)

**Learning Format Going Forward:**
- **Design-only days** (Days 33-35): Create `.md` file with bottleneck analysis, decisions, tradeoffs. Quick, no communication coaching.
- **Coaching days** (occasional): Full bottleneck-first questioning, interview practice, communication feedback.
- **Implementation days** (future): Code the system design with tests.

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
| Day 31 | **Notification System Refined** | Medium | Idempotency, priority batching, regional failover, DR | 50 min |
| Day 32 | **Redis-Style KV Store** | Medium | RDB + AOF persistence, LFU eviction, critical data protection | 40 min |
| Day 33 | **Search Engine (basic)** | Medium | Indexing, ranking, inverted index, distributed search | 45 min |
| Day 34 | **Leaderboard/Rankings System** | Medium | Sorted sets, real-time updates, scalability | 35 min |
| Day 35 | **Checkpoint Assessment Day** | N/A | ✅ DONE 2026-09-08 — scored 6.0/10, NOT ready for Phase 3 | 75 min |

### Phase 2.5: BRIDGE (Days 36-42) — Added after the Day 35 checkpoint
**Goal:** Close the two failed criteria (consistency depth, multi-constraint reasoning) before Hard systems

| Day | System/Topic | Difficulty | Focus | Time |
|-----|--------------|------------|-------|------|
| Day 36 | **Consistency Models (mechanism-first)** | Medium | Read-your-own-writes, monotonic reads, causal, linearizable — worked examples before design questions | 45 min |
| Day 37 | **Search Engine — finish Day 33** | Medium | Ranking, sharding, freshness, tenant isolation | 45 min |
| Day 38 | **Applied Session — Xe Rate Alerts** (not on roadmap) | Medium | Scaled own take-home to production: batching, outbox, broker vs direct-publish tradeoffs | ~90 min |
| Day 39 | **Consistency re-test** | Medium | ✅ DONE 2026-09-17 — 8.2/10, gate cleared | 40 min |
| Day 40 | **Bottleneck-confidence drill** (new, requested 2026-09-17) | Medium | ✅ DONE 2026-09-18 — 7.0/10, not a gate day; pattern broken within-session once verdict/headroom/risk were forced into separate sentences | 40 min |
| Day 41 | **Multi-constraint drill** | Hard | 3 scenarios with conflicting constraints. Name the pair, price the relaxation. Gate: ≥7/10 | 50 min |
| Day 42 | **Round 6 + full re-assessment** | Hard | Real-time/strong consistency round, then re-score all 6 criteria | 60 min |

**Phase 3 gate:** consistency ≥ 8/10 (✅ cleared Day 39) AND multi-constraint ≥ 7/10 on Day 41.

**Standing drill from Day 36 onward** — before designing anything, ask:
*"What in this brief am I taking as given that I should be challenging?"*

### Phase 3: HARD (Days 43-52) — 45-60 mins each
**Goal:** Master complex tradeoffs, real-time systems, strong consistency

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 43 | **Uber (Ride Sharing)** | Hard | Geolocation, real-time matching, strong consistency | 60 min |
| Day 44 | **YouTube (Video Streaming)** | Hard | Storage, CDN, transcoding, distributed encoding | 60 min |
| Day 45 | **Google Maps** | Hard | Geospatial indexing, routing, real-time traffic | 55 min |
| Day 46 | **Slack (Workspace Platform)** | Hard | Real-time messaging, presence, search | 60 min |
| Day 47 | **Stripe (Payment System)** | Hard | Strong consistency, reliability, compliance, idempotency | 60 min |
| Day 48 | **Discord (Real-time Chat)** | Hard | Message ordering, consistency, reliability, presence | 60 min |
| Day 49 | **Netflix (Video Service)** | Hard | Recommendation, streaming, CDN, global distribution | 60 min |
| Day 50 | **Amazon S3 (Object Storage)** | Hard | Distributed storage, replication, consistency | 55 min |
| Day 51 | **GitHub (Code Collaboration)** | Hard | Version control, branching, conflict resolution | 60 min |
| Day 52 | **Kafka (Event Streaming)** | Hard | Partitioning, ordering, replication, fault tolerance | 60 min |

### Phase 4: VERY HARD (Days 53-62) — 60+ mins each
**Goal:** Design complex, multi-faceted distributed systems

| Day | System | Complexity | Focus | Approx Time |
|-----|--------|-----------|-------|------------|
| Day 53 | **Google Drive (Cloud Storage + Sync)** | Very Hard | Sync protocols, conflict resolution, eventual consistency | 70 min |
| Day 54 | **Airbnb (Marketplace)** | Very Hard | Search, inventory, transactions, trust, payments | 75 min |
| Day 55 | **DynamoDB (NoSQL Database)** | Very Hard | Distributed hash table, replication, auto-scaling | 70 min |
| Day 56 | **Cassandra (Distributed DB)** | Very Hard | Ring topology, eventual consistency, read repair | 75 min |
| Day 57 | **Facebook (Social Network)** | Very Hard | Graph DB, privacy, real-time notifications | 75 min |
| Day 58 | **LinkedIn (Connections + Feed)** | Very Hard | Graph algorithms, feed ranking, job recommendations | 70 min |
| Day 59 | **Evernote (Note Taking + Sync)** | Very Hard | Rich content, encryption, offline-first, sync | 70 min |
| Day 60 | **Dropbox (File Sync Service)** | Very Hard | Delta sync, versioning, conflict resolution | 75 min |
| Day 61 | **Docker Registry (Container Storage)** | Very Hard | Distributed image storage, layering, replication | 70 min |
| Day 62 | **AWS Lambda (Serverless)** | Very Hard | Scheduling, scaling, cold starts, isolation | 75 min |

### Phase 5: YOUR REAL APP (Days 63-72) — Custom duration
**Goal:** Design critical systems for your SaaS+Fintech platform

| Day | System | Your Pain Point | Focus | Approx Time |
|-----|--------|------------------|-------|------------|
| Day 63 | **Reporting System** | Reports hanging | Async processing, materialized views, caching | 45 min |
| Day 64 | **Data Pipeline (ETL)** | Real-time analytics | Streaming, batching, incremental updates | 50 min |
| Day 65 | **User Onboarding Flow** | Conversion optimization | Multi-step, validation, emails, notifications | 40 min |
| Day 66 | **Payment Processing** | Fintech core | Transactions, retries, idempotency, audit | 60 min |
| Day 67 | **Search/Autocomplete** | User experience | Indexing, ranking, real-time suggestions | 45 min |
| Day 68 | **Audit Logging (Enhanced)** | Compliance | Tamper-proof logs, compliance reporting | 40 min |
| Day 69 | **Analytics Dashboard** | Business intelligence | Real-time metrics, aggregations, visualizations | 50 min |
| Day 70 | **Multi-region Replication** | Global expansion | Data consistency, conflict resolution | 55 min |
| Day 71 | **Disaster Recovery System** | Business continuity | Backup, restore, failover, testing | 50 min |
| Day 72 | **Migration from Legacy** | Technical debt | .NET Framework → .NET 8, session → JWT | 60 min |

### Phase 6: ADVANCED TOPICS (Days 73+) — Optional deep dives
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
Week 5-7 (Days 36-46): Hard systems, deep tradeoff analysis
Week 8-10 (Days 47-56): Very hard systems, multi-dimensional thinking
Week 11-13 (Days 57-66): Your real app systems, practical application
Week 14+: Advanced topics or specialized deep dives
```

---

**Status Legend:** ⬜ Not Started &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ✅ Done
