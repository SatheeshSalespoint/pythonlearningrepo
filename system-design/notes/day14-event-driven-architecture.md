# Day 14 — Event-Driven Architecture (EDA)

**Date:** 2026-08-03
**Time:** 15 minutes

---

## The Problem — Tight Coupling

In direct service-to-service calls, every producer must know every consumer. Adding a new reaction to an event means modifying the producer. Services become tightly coupled.

```
  OrderService.PlaceOrder()
      │
      ├──▶ InventoryService.Reserve()     ← must call directly
      ├──▶ NotificationService.SendEmail() ← must call directly
      ├──▶ AnalyticsService.TrackOrder()   ← must call directly
      └──▶ LoyaltyService.AwardPoints()    ← must call directly

  Problem: Order service knows about (and depends on) every downstream service.
  Adding a new consumer = modify Order service + redeploy.
```

---

## The Solution — Event-Driven Architecture

Instead of calling consumers directly, the producer **emits an event** — a fact that something happened. Consumers listen and react independently.

```
  OrderService.PlaceOrder()
      │
      └──▶ Publish: OrderPlaced { orderId, total, items }
                        │
                        ▼
               [Event Broker / Bus]
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
   InventoryService  NotificationSvc  AnalyticsService
   (reserves stock)  (sends email)    (tracks metrics)

  Adding LoyaltyService? Just add a new consumer — Order service unchanged.
```

> **Core principle:** Producers emit *facts*, consumers react *independently*. No direct dependency between them.

---

## Core Components

| Component | Role | Examples |
|-----------|------|---------|
| **Producer** | Emits events when something happens | Order service, Payment service |
| **Event Broker** | Routes, stores, and delivers events | Kafka, Azure Service Bus, RabbitMQ, AWS EventBridge |
| **Consumer** | Subscribes to events and reacts | Inventory, Notification, Analytics services |
| **Event** | Immutable record of what happened | `OrderPlaced`, `PaymentFailed`, `UserRegistered` |

---

## What Is an Event?

An event is a **past-tense fact** — something that already happened. It is immutable; you never edit history.

```json
{
  "eventType": "OrderPlaced",
  "eventId": "evt-7a3f2c",
  "occurredAt": "2026-08-03T11:15:00Z",
  "correlationId": "req-abc-123",
  "data": {
    "orderId": "ord-456",
    "customerId": "cust-789",
    "items": [{ "sku": "PROD-001", "qty": 2 }],
    "total": 99.90
  }
}
```

**Naming convention:** Always use past tense — `OrderPlaced`, not `PlaceOrder`. Commands are requests; events are facts.

---

## Two Flavours of Events

### 1. Event Notification — "Something happened, go look it up"

```json
{ "eventType": "OrderPlaced", "orderId": "ord-456" }
```

- Consumer receives event, then **calls back** to Order service for full details
- Keeps events small
- ⚠️ Consumer now depends on Order service being available → some coupling remains

### 2. Event-Carried State Transfer — "Here's everything you need"

```json
{
  "eventType": "OrderPlaced",
  "orderId": "ord-456",
  "customerId": "cust-789",
  "items": [...],
  "total": 99.90
}
```

- Consumer is **fully autonomous** — no extra call needed
- Larger payload, but consumers are truly decoupled
- ✅ Preferred for microservices when autonomy matters

> **Rule of thumb:** Use state transfer for autonomy; use notification when events contain sensitive data that shouldn't be broadcast.

---

## EDA vs Message Queues — The Difference

This builds directly on Day 7. The concepts overlap but solve different problems:

| | Message Queue | Event-Driven Architecture |
|---|---|---|
| **Focus** | Task dispatch — get work done | Broadcasting facts — inform who cares |
| **Pattern** | Point-to-point (one consumer) | Pub/Sub (many consumers) |
| **Guarantee** | One consumer processes the message | All subscribers receive the event |
| **Example** | "Process this payment charge" | "Payment completed — everyone react" |
| **Tools** | RabbitMQ task queue, MassTransit | Kafka, Azure Event Grid, AWS EventBridge |

> Message queues are a **tool**; EDA is an **architectural pattern** that often uses them.

---

## Why Use EDA

| Benefit | What It Means |
|---------|---------------|
| **Loose coupling** | Producer doesn't know or care about consumers |
| **Independent scaling** | High-traffic consumers (analytics) scale without affecting others |
| **Resilience** | Producer succeeds even if a consumer is temporarily down |
| **Extensibility** | Add new consumers with zero changes to producer |
| **Audit trail** | Event log = natural audit of everything that happened |

---

## The Hard Parts

### 1. No Immediate Feedback

```
  Traditional:   Order → calls → Payment → returns "Charged OK" ✅
  EDA:           Order → emits → OrderPlaced → ... silence

  How do you know if Inventory failed to reserve stock?
```

**Solutions:**
- Use **correlation IDs** to trace flows across services
- Use **reply topics** — consumer publishes `InventoryReserved` or `InventoryFailed` back
- Use the **Saga pattern** for multi-step workflows requiring coordination (Day 16 territory)

---

### 2. Duplicate Events — Consumers Must Be Idempotent

Networks fail and retry. The same event may be delivered **more than once**.

```
  Event: OrderPlaced { orderId: "ord-456" }

  Consumer receives it twice:
    → Sends confirmation email twice  ❌
    → Charges payment twice           ❌ (catastrophic)
    → Reserves inventory twice        ❌
```

**Idempotency fix — track processed event IDs:**

```csharp
public async Task Consume(ConsumeContext<OrderPlaced> context)
{
    var eventId = context.Message.EventId;

    if (await _processedEvents.ExistsAsync(eventId))
        return; // already handled — skip safely

    await _emailService.SendOrderConfirmation(context.Message.OrderId);
    await _processedEvents.MarkAsync(eventId);
}
```

> **Rule:** Every EDA consumer **must be idempotent**. Processing the same event twice must produce the same result as processing it once.

---

### 3. Event Ordering

Kafka guarantees ordering **per partition** only. If two events for the same order land on different partitions:

```
  Partition 0: OrderCancelled { orderId: "ord-456" }  ← arrives first
  Partition 1: OrderPlaced    { orderId: "ord-456" }  ← arrives second

  Consumer processes Cancel before Placed → bugs
```

**Fixes:**
- Use the **entity ID as the partition key** → all events for the same order go to the same partition → ordered
- Design consumers to handle out-of-order events gracefully (check current state before acting)

---

### 4. Eventual Consistency

```
  User places order at 11:00:00
  Inventory service processes OrderPlaced event at 11:00:02

  At 11:00:01 — inventory not yet updated.
  User checks stock level → still shows old value.
```

This is **by design** in EDA. Embrace it:
- Show "Your order is being processed" rather than a live inventory count
- Design UIs around async feedback (order status page, email confirmations)
- Only fight eventual consistency where it truly matters (e.g. payments — use synchronous calls there)

---

## Real-World .NET Example — MassTransit + Azure Service Bus

```csharp
// Define the event (shared contract — often in a separate NuGet package)
public record OrderPlaced(
    Guid EventId,
    Guid OrderId,
    Guid CustomerId,
    decimal Total,
    DateTimeOffset OccurredAt);

// ─────────────────────────────────────────
// PRODUCER — Order Service
// ─────────────────────────────────────────

public class OrderService(IPublishEndpoint publishEndpoint)
{
    public async Task PlaceOrderAsync(Order order)
    {
        // ... save order to DB ...

        await publishEndpoint.Publish(new OrderPlaced(
            EventId: Guid.NewGuid(),
            OrderId: order.Id,
            CustomerId: order.CustomerId,
            Total: order.Total,
            OccurredAt: DateTimeOffset.UtcNow));
        // Done — doesn't know or care who handles this
    }
}

// ─────────────────────────────────────────
// CONSUMER A — Notification Service (separate service/project)
// ─────────────────────────────────────────

public class OrderPlacedConsumer(IEmailService emailService, IProcessedEventStore store)
    : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        var msg = context.Message;

        if (await store.ExistsAsync(msg.EventId))
            return; // idempotency guard

        await emailService.SendConfirmation(msg.CustomerId, msg.OrderId);
        await store.MarkAsync(msg.EventId);
    }
}

// ─────────────────────────────────────────
// CONSUMER B — Inventory Service (completely independent)
// ─────────────────────────────────────────

public class OrderPlacedInventoryConsumer(IInventoryService inventory)
    : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        await inventory.ReserveStockAsync(context.Message.OrderId);
    }
}
```

Zero direct dependency between Order Service and Notification/Inventory services. ✅

---

## Connection to Previous Days

| Topic | How EDA Relates |
|-------|-----------------|
| **Day 7 — Message Queues** | Queues are the transport layer EDA often uses (Kafka, RabbitMQ) |
| **Day 11 — Microservices** | EDA is the primary decoupling strategy between microservices |
| **Day 13 — Circuit Breaker** | Consumers should use CB when calling downstream services inside event handlers |
| **Day 8 — Rate Limiting** | Consumer processing rate can be throttled to protect downstream services |

---

## When to Use EDA

| ✅ Good Fit | ❌ Bad Fit |
|---|---|
| Multiple services react to the same business event | You need immediate confirmation (card charge) |
| High-volume async workflows (orders, notifications) | Simple CRUD with 1-2 services — massive overkill |
| Adding new consumers without touching producers | Your team struggles with distributed debugging |
| Audit log / event history is a requirement | Strong consistency required across the board |
| Services owned by different teams | Low traffic, single deployment unit |

---

## When NOT to Use EDA — The Common Mistake

**Payments are the classic exception.** Never make a charge fire-and-forget:

```
❌ Wrong:
  OrderService publishes OrderPlaced → PaymentService eventually charges card
  User gets "Order confirmed" before payment succeeds
  Payment fails silently → order fulfilled, revenue lost

✅ Right:
  OrderService calls PaymentService synchronously → success → then publishes OrderPlaced
  Payment result known immediately → charge guaranteed before downstream events fire
```

> **Rule:** Money movement, stock allocation, and any action with real-world consequences that must succeed or fail atomically — keep synchronous. Use EDA for downstream reactions to confirmed facts.

---

## 🎯 Key Takeaway

> **EDA = producers emit past-tense facts (`OrderPlaced`), consumers react independently. Design events as immutable records, make every consumer idempotent (duplicate delivery is guaranteed), partition by entity ID for ordering, and embrace eventual consistency. Keep payment charges synchronous — publish events only after the critical action succeeds.**

---

## Questions to Think About

1. Your Order service publishes `OrderPlaced`. Both Inventory and Notification consume it. Notification is down for 2 minutes. What happens to those events? What must the broker guarantee — and what must Notification guarantee when it comes back up?
2. You have an `OrderPlaced` event. Inventory needs: orderId, items, quantities. Notification needs: orderId, customerId, email, total. Do you put all fields in one event or create two separate events? What are the trade-offs?
3. A consumer processes an `OrderPlaced` event, reserves inventory, then crashes before marking the event as processed. The broker redelivers the event. Walk through what happens — and what design choice prevents a double-reservation.

---

## Q&A Insights — 2026-08-03

### CorrelationId vs EventId (IdempotencyKey)

These solve different problems and must not be confused:

| | CorrelationId | EventId (IdempotencyKey) |
|---|---|---|
| **Purpose** | Trace a flow across services (logging, AppInsights) | Detect duplicate delivery of the same event |
| **Scope** | Shared across multiple events in one flow | Unique per event instance |

```
User places order → correlationId = "req-abc"
  OrderPlaced    { eventId: "evt-001", correlationId: "req-abc" }
  PaymentCharged { eventId: "evt-002", correlationId: "req-abc" }
  StockReserved  { eventId: "evt-003", correlationId: "req-abc" }

Broker redelivers OrderPlaced:
  Consumer checks eventId "evt-001" → already seen → skip ✅
  If checked correlationId "req-abc" instead → would skip ALL 3 events ❌
```

> CorrelationId is 1:many across events. EventId is 1:1 per delivery. They are not interchangeable.

---

### RabbitMQ Fanout — Each Consumer Needs Its Own Named Durable Queue

In fanout mode, RabbitMQ copies the message into each bound queue at publish time. Inventory ACKing clears it from the inventory queue only — the notification queue is fully independent.

```
Fanout Exchange
    ├──▶ Queue: inventory-orderplaced   (durable)
    └──▶ Queue: notification-orderplaced (durable)
```

**Critical:** queues must be **named and durable**. A transient/anonymous queue disappears on consumer disconnect — those 2 minutes of events are gone forever.

---

### Event Field Ownership — Don't Put `email` in OrderPlaced

`email` is owned by Customer service, not Order service. Including it in `OrderPlaced` causes stale data if the customer updates their email.

```json
// ✅ Correct — only fields Order service owns
{
  "eventType": "OrderPlaced",
  "orderId": "ord-456",
  "customerId": "cust-789",   ← Order service owns this relationship
  "items": [...],
  "total": 99.90
  // email ❌ — Customer service owns this
}
```

**Notification service gets email autonomously:**
- Customer service publishes `CustomerRegistered { customerId, email }`
- Notification service consumes it → stores locally
- On `OrderPlaced` → looks up email from its own DB ✅ fully autonomous, always fresh

---

### Idempotency Requires Atomic Transaction — Not Two Separate Writes

Storing the EventId separately from the business operation creates a crash window:

```
❌ Broken:
  1. Reserve inventory in DB
  2. 💥 Crash
  3. EventId never saved → redelivery causes double reservation

✅ Correct — single transaction:
  BEGIN TX
    INSERT INTO processed_events (event_id) -- UNIQUE constraint
    UPDATE inventory SET reserved_qty = reserved_qty + qty
  COMMIT
```

- Crash before commit → both rolled back → retry is safe
- Crash after commit → both saved → redelivery is skipped

> **Rule:** EventId storage and the business operation must commit in the same transaction. Two separate writes with a crash window between them is not idempotency.
