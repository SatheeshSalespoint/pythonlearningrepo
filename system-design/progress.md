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
| Day 9 | CDN & Static Assets | ⬜ | | |
| Day 10 | Database Indexing & Query Optimisation | ⬜ | | |
| Day 11 | Microservices vs Monolith | ⬜ | | |
| Day 12 | Service Discovery | ⬜ | | |
| Day 13 | Circuit Breaker Pattern | ⬜ | | |
| Day 14 | Event-Driven Architecture | ⬜ | | |
| Day 15 | CQRS Pattern | ⬜ | | |
| Day 16 | Event Sourcing | ⬜ | | |
| Day 17 | Consistent Hashing | ⬜ | | |
| Day 18 | Database Sharding | ⬜ | | |
| Day 19 | Replication — Leader/Follower | ⬜ | | |
| Day 20 | Designing a URL Shortener (case study) | ⬜ | | |

---

**Status Legend:** ⬜ Not Started &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ✅ Done
