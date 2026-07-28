# Day 11 — Microservices vs Monolith

**Date:** 2026-07-29  
**Time:** 15 minutes  

---

## The Monolith

A single deployable unit — all features in one codebase, one process, one database.

```
┌──────────────────────────────────────┐
│           Monolith                   │
│  ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │ Orders │ │  Users │ │ Payments │  │
│  └────────┘ └────────┘ └──────────┘  │
│              ↓                       │
│         Single DB                    │
└──────────────────────────────────────┘
```

### Strengths
- Simple to develop, test, debug, and deploy early on
- Low operational overhead — one CI/CD pipeline
- Easy cross-module transactions (just a DB transaction)
- No network latency between modules

### Weaknesses
- One bad deploy takes everything down
- Can't scale parts independently (scaling Orders forces scaling everything)
- Teams step on each other in one big codebase over time
- Deployment risk grows as codebase grows

---

## Microservices

Each business domain is its own independently deployable service with its own database.

```
  [API Gateway]
      │
  ┌───┴──────────────────────┐
  ▼           ▼              ▼
[Orders]   [Users]       [Payments]
  │           │              │
 DB-O        DB-U           DB-P
```

### Strengths
- Independent deployments — ship Orders without touching Payments
- Scale only what's under load (K8s scales Payments pods during checkout)
- Tech stack freedom per service
- Fault isolation — one service crashes, others survive

### Weaknesses
- **Distributed transactions are hard** — no shared DB transaction
- Network latency & failures between services
- Much higher operational complexity (service mesh, observability, K8s)
- Data consistency challenges (eventual consistency)

---

## Shared DB with Microservices — Anti-Pattern ❌

```
  [Orders Service]   [Payments Service]   [Users Service]
         │                  │                   │
         └──────────────────┴───────────────────┘
                            │
                     ┌──────────────┐
                     │  Shared DB   │
                     └──────────────┘
```

This is called a **Distributed Monolith** — worst of both worlds:

| Problem | Why |
|---------|-----|
| Tight coupling via schema | Orders changes a table → breaks Payments |
| No independent deployability | Schema migration requires coordinating all teams |
| No fault isolation | DB goes down → every service goes down |
| Scaling still coupled | Can't scale DB for just one service's load |

### The One Exception ✅

A **read-only analytics/reporting DB** — all services write events to it, but no service owns or mutates its state.

```
Orders → [Event Bus] → [Analytics DB] ← Reports Service
Payments ↗
```

---

## Scaling — Monolith vs Microservices

Both support **vertical and horizontal** scaling. The difference is **granularity**.

### Monolith Horizontal Scaling — All or Nothing

```
            [Load Balancer]
           /       |        \
    [Monolith]  [Monolith]  [Monolith]
    Instance 1  Instance 2  Instance 3
```

Scale Orders load? You must also spin up extra Payments, Users, etc. — even if they're idle. **Wasteful.**

### Microservices Horizontal Scaling — Selective ✅

```
Black Friday:
  Orders    → scale to 10 instances  (needed 🔥)
  Payments  → scale to 8 instances   (needed 🔥)
  Users     → stays at 1 instance    (quiet 😴)
```

Scale only what's hot. Everything else stays small.

---

## Cost: Horizontal vs Vertical

### Vertical Scaling — Exponential Cost Curve 📈

```
2 CPU / 4GB  →  $20/mo
8 CPU / 32GB →  $200/mo    (4x resource, 10x cost!)
32 CPU/128GB →  $1500/mo   (further exponential jump)
```

High-end servers carry a premium price curve — not linear.

### Horizontal Scaling — Linear Cost 📊

```
1 × small instance = $20/mo
5 × small instance = $100/mo  (5x resource, 5x cost ✅)
```

Commodity hardware scales linearly. Cloud auto-scaling spins up/down on demand.

### But Microservices Have Hidden Costs ⚠️

| Cost | Detail |
|------|--------|
| Minimum instances per service | 3 services × 2 min instances = 6 always running |
| Infra overhead | K8s, service mesh, observability tooling |
| Engineering time | More complex to build and maintain |

> **Small systems:** Monolith is often cheaper.  
> **Large systems at scale:** Microservices selective scaling wins.

---

## The Real Decision Framework

| Signal | Go Monolith | Go Microservices |
|--------|-------------|------------------|
| Team size | < 10 engineers | Multiple independent teams |
| Scale needs | Uniform load | Wildly uneven load per feature |
| Release pace | Infrequent, batched | Teams need independent deploys |
| Domain maturity | Domain boundaries unclear | Well-defined bounded contexts |
| Ops capability | Minimal DevOps | Strong K8s/observability culture |

---

## The Pattern Senior Devs Use: Modular Monolith First

```
Start:  Modular Monolith
          → clear module boundaries, no shared internals
          → each module owns its data (logical separation)

Later:  Extract a service ONLY when you have:
          ✅ Team ownership boundary
          ✅ Independent scale requirement
          ✅ Deployment friction costing you real time
```

> Netflix, Uber, Amazon — **all started as monoliths.** They extracted services at team/scale pain points, not upfront.

---

## C# Angle

- **Monolith done right:** Separate class libraries per domain, clean interfaces — extracting later is easy
- **Microservices in .NET:** Each service is its own ASP.NET Core app
  - Async communication: `MassTransit` (RabbitMQ / Azure Service Bus)
  - Sync communication: `Refit` / `HttpClientFactory`
- **Distributed transactions:** Use the **Saga pattern** (choreography or orchestration via MassTransit)

```csharp
// MassTransit Saga — Orchestration example
public class OrderSaga : MassTransitStateMachine<OrderSagaState>
{
    public OrderSaga()
    {
        Initially(
            When(OrderPlaced)
                .Then(ctx => ctx.Saga.OrderId = ctx.Message.OrderId)
                .TransitionTo(AwaitingPayment)
                .Publish(ctx => new ProcessPayment { OrderId = ctx.Saga.OrderId })
        );

        During(AwaitingPayment,
            When(PaymentCompleted)
                .TransitionTo(Completed)
                .Publish(ctx => new ShipOrder { OrderId = ctx.Saga.OrderId }),
            When(PaymentFailed)
                .TransitionTo(Failed)
                .Publish(ctx => new CancelOrder { OrderId = ctx.Saga.OrderId })
        );
    }
}
```

---

## Quick Comparison Table

| Dimension | Monolith | Microservices |
|-----------|----------|---------------|
| Deployment | Single unit | Independent per service |
| Scaling | All-or-nothing | Granular per service |
| Transactions | Simple DB tx | Saga / eventual consistency |
| Latency | None (in-process) | Network hops between services |
| Ops complexity | Low | High |
| Best for | Early stage / small teams | Large teams / uneven scale |

---

## 🎯 Key Takeaway

> **Start with a well-structured modular monolith. Microservices are an organisational scaling solution — they solve team and deployment boundary problems, not just technical load. Extract services when the pain is real (team conflict, deployment friction, uneven scale), not upfront. Shared DB + microservices = distributed monolith — always give each service its own database.**

---

## Questions to Think About

1. You have a monolith with Orders, Payments, and Inventory modules. Traffic to Orders is 50× higher than Payments. What's the scaling problem and how do microservices solve it?
2. Your team decides to split into microservices but keep a single shared database to "simplify things." What problems will you face in 6 months?
3. You need to place an order (deduct inventory + charge payment + create order record). In a monolith this is one DB transaction. How do you handle this across 3 microservices?
