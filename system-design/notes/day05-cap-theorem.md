# Day 5 — CAP Theorem

**Date:** 2026-07-17  
**Time:** 15 minutes  

---

## What Is CAP Theorem?

In any **distributed system**, you can only guarantee **2 of these 3** properties simultaneously:

| Letter | Property | Meaning |
|--------|----------|---------|
| **C** | Consistency | Every read gets the most recent write (or an error) |
| **A** | Availability | Every request gets a response (no errors, maybe stale data) |
| **P** | Partition Tolerance | System works even if nodes can't talk to each other |

---

## The Key Insight

**Network partitions always happen** in real distributed systems (cables fail, network blips, data centre splits).  
So **P is non-negotiable** → the real choice is always: **CP vs AP**

```
Real choice:
  CP — Consistency + Partition Tolerance  →  correct data or error
  AP — Availability + Partition Tolerance →  response always, maybe stale
```

---

## CP vs AP — When to Choose What

**CP (Consistency + Partition Tolerance)**
> "Give me correct data or give me an error"

- ✅ Banking, payments, seat booking, inventory allocation
- Examples: **HBase, Zookeeper, MongoDB (strong write concern)**
- .NET context: SQL Server with synchronous mirroring = CP

**AP (Availability + Partition Tolerance)**
> "Give me *some* response even if it might be slightly stale"

- ✅ Social media feeds, product catalogues, service registries, DNS
- Examples: **Cassandra, DynamoDB (eventual), Eureka**
- .NET context: Redis cache serving stale data during DB outage = AP

---

## CAP Is Not Just Databases

CAP applies to **any distributed system** that shares state across nodes — including microservices.

| Microservice Concern | CP approach | AP approach |
|---|---|---|
| Service-to-service calls | Fail fast, return error | Return cached/stale response |
| Service registry (discovery) | Zookeeper — blocks if no quorum | Eureka — serves stale list |
| Distributed config | Block until consistent | Serve last known config |
| Distributed transactions | 2-Phase Commit (slow, safe) | Saga + compensating transactions |
| API Gateway cache | Bypass cache, hit origin | Serve cache during outage |

> Netflix replaced Zookeeper with **Eureka (AP)** because a CP registry going down during partition caused cascading failures across all services.

---

## Same System, Different Choices Per Operation

Modern systems like **DynamoDB, Cosmos DB** let you configure consistency **per request**. The same service can be AP for reads and CP for writes.

### E-commerce Cart Example

```
Adding items to cart  →  AP
  └── Stale cart across devices for a few seconds = fine

Checkout / Payment    →  CP
  └── Must verify stock, price, and payment atomically
  └── Partition → return error, don't process
```

---

## Real-World Decision Guide

```
Is wrong data catastrophic?
  YES → CP (payments, seat booking, stock allocation)
  NO  → AP (feeds, catalogue, session data, service discovery)
```

| System | Choice | Reason |
|---|---|---|
| Payment processing | CP | Double-spend / overdraft risk |
| Airline seat booking | CP | Two passengers, one seat |
| Social media feed | AP | 2-second stale feed is fine |
| Product catalogue | AP | Price stale by seconds, acceptable |
| Service registry | AP | Stale list beats no list (cascading failures) |
| E-commerce cart | AP | Cart sync delay is acceptable |
| E-commerce checkout | CP | Inventory + payment must be accurate |

---

## Partition Tolerance in Practice

Redirection and multi-region failover **reduce** the chance of hitting a partition scenario but don't eliminate it. When a true partition occurs:

```
Redirect to another data centre → works if that node has consistent data (CP)
Serve from local node → works but may be stale (AP)
```

Good distributed design **minimises** partition impact via replication and failover, then **chooses CP or AP** for the unavoidable cases.

---

## 🎯 Key Takeaway

> **P is unavoidable. Pick CP for correctness (finance/inventory), AP for resilience (feeds/discovery).**  
> The same system can be AP for browsing and CP for transactions — tune per operation where possible.

---

## Questions to Think About

1. Your current C# API — if a network partition occurred, would you rather return an error or serve stale data? What does that tell you about your CP/AP stance?
2. Think of one service in your system that should be CP and one that should be AP. What changes if you swap them?
3. If you were building a stock trading platform, which operations are CP and which could tolerate AP?
