# Day 7 — Message Queues & Async Communication

**Date:** 2026-07-21  
**Time:** 15 minutes  

---

## The Problem Async Solves

Synchronous calls couple services tightly:

```
OrderService → HTTP → InventoryService → HTTP → EmailService
```

If EmailService is slow or down → the whole order fails. That's brittle.

**Solution:** Decouple with a message queue.

```
Order API → save order → publish event → return 200 ✅ (fast)
                ↓
         [Message Queue]
         ↙      ↓       ↘
      Email  Inventory  Warehouse  (async, decoupled)
```

---

## Core Concepts

### Producer / Consumer Pattern

```
OrderService (Producer) → [Queue] → EmailService (Consumer)
                                  → InventoryService (Consumer)
```

- Producer fires and forgets
- Consumers process at their own pace
- Queue absorbs traffic spikes

### Key Terms

| Term | Meaning |
|------|---------|
| **Queue** | Point-to-point — one consumer gets the message |
| **Topic/Exchange** | Pub/sub — many consumers get the same message |
| **Dead Letter Queue (DLQ)** | Failed messages land here for retry/analysis |
| **Ack/Nack** | Consumer confirms (ack) or rejects (nack) — prevents message loss |

---

## When to Use Async

✅ Long-running work (send email, process PDF, resize image)  
✅ Traffic spike buffering  
✅ Fan-out (one event → multiple services react)  
✅ Retry logic with backoff  

❌ **Don't use** when you need an immediate response — use sync HTTP/gRPC instead

---

## RabbitMQ vs Kafka

| | RabbitMQ | Kafka |
|--|----------|-------|
| **Model** | Smart broker, dumb consumer | Dumb broker, smart consumer |
| **Message retention** | Deleted after ack | Retained for N days (replayable) |
| **Ordering** | Per queue | Per partition |
| **Throughput** | Moderate | Extremely high |
| **Use case** | Task queues, RPC | Event streaming, audit log, replay |

> C# context: Azure Service Bus ≈ RabbitMQ model. Azure Event Hubs ≈ Kafka model.

---

## Channel\<T\> — In-Process Queue

`Channel<T>` (System.Threading.Channels) is a legitimate in-process async queue — no broker, no infrastructure.

```csharp
// Producer
await _channel.Writer.WriteAsync(new OrderEvent { ... });

// Consumer (BackgroundService)
await foreach (var msg in _channel.Reader.ReadAllAsync())
{
    await ProcessAsync(msg);
}
```

### Channel\<T\> vs External Queue

| Concern | `Channel<T>` | RabbitMQ / Kafka |
|---------|-------------|-----------------|
| **Scope** | In-process only | Cross-process / cross-machine |
| **Durability** | ❌ Lost on crash | ✅ Persisted to disk |
| **Scale-out** | ❌ One instance only | ✅ Multiple consumer instances |
| **Retry / DLQ** | ❌ Manual | ✅ Built-in |
| **Throughput** | Millions/sec (in-RAM) | 50k–1M/sec (network) |
| **Latency** | Nanoseconds | Milliseconds |

### Safe Pattern — DB/Redis First

```
Service A → writes to DB/Redis  ← durable ✅
               ↓
           Channel<T>  ← triggers processing (signal only)
               ↓
           Service B reads from DB/Redis
```

State lives in DB/Redis, not in the channel. If app restarts → recover by re-querying unprocessed records on startup.

### Always Use BoundedChannel in Production

```csharp
var channel = Channel.CreateBounded<OrderEvent>(new BoundedChannelOptions(1000)
{
    FullMode = BoundedChannelFullMode.Wait  // backpressure
});
```

`CreateUnbounded` grows until OOM. Always cap it.

---

## MassTransit

MassTransit is an **abstraction layer** over message brokers — like EF Core is to databases.

```
Your C# Code
     ↓
  MassTransit  ← library (abstraction)
     ↓
RabbitMQ / Kafka / Azure Service Bus / Amazon SQS
```

### Raw RabbitMQ vs MassTransit

```csharp
// Raw — verbose, manual everything
channel.BasicPublish("", "orders", null, body);

// MassTransit — clean, broker-agnostic
await _bus.Publish(new OrderCreated { OrderId = 123 });
```

### What MassTransit Gives You

| Feature | Raw Broker | MassTransit |
|---------|-----------|-------------|
| Retry with backoff | ❌ Build it | ✅ Built-in |
| Dead letter queue | ❌ Manual | ✅ Auto `_error` queue |
| Correlation / tracing | ❌ Manual headers | ✅ Auto CorrelationId |
| Saga / state machine | ❌ Build it | ✅ First-class support |
| Outbox pattern | ❌ Build it | ✅ Built-in |
| Swap broker | ❌ Rewrite | ✅ Change one config line |

### Opt-In Features

| Feature | Effort |
|---------|--------|
| **Retries** | ~2 lines config — applies globally to all consumers |
| **DLQ** | Zero — automatic `_error` queue |
| **Outbox** | Medium — needs DB table + EF setup |
| **Sagas** | High — you design the state machine |

```csharp
// Retries — global config
cfg.UseMessageRetry(r => r.Intervals(1000, 5000, 30000));

// Outbox — needs DB
x.AddEntityFrameworkOutbox<AppDbContext>(o => {
    o.UseSqlServer();
    o.UseBusOutbox();
});

// Saga — you define states and transitions
public class OrderStateMachine : MassTransitStateMachine<OrderState>
{
    public OrderStateMachine()
    {
        Initially(When(OrderSubmitted).TransitionTo(AwaitingPayment));
        During(AwaitingPayment, When(PaymentReceived).TransitionTo(Completed));
    }
}
```

---

## Outbox Pattern

Solves the **dual write problem**:

```
Save to DB   ✅
App crashes 💥
Publish event ❌ ← never happens — downstream never knows
```

**Fix:**
```
DB Transaction (atomic):
  ├── INSERT orders
  └── INSERT outbox_messages (status = pending)

Background job:
  SELECT pending → publish to broker → mark published
```

Both writes in one transaction — crash-safe.

---

## Fanout (Broadcast)

One message → **every subscriber gets a copy**.

```
OrderPlaced event
      ↓
[Fanout Exchange]
 ↙        ↓         ↘         ↘
EmailSvc  InventorySvc  WarehouseSvc  AnalyticsSvc
(each gets full copy ✅)
```

### Fanout vs Competing Consumer

| | Competing Consumer | Fanout |
|--|---|---|
| **Who gets message** | ONE instance | ALL instances |
| **Purpose** | Do the work once | React independently |
| **Scale** | Add more instances | Add more consumer types |
| **Example** | Process payment | Invalidate cache across instances |

### Combined in Real Systems

```
OrderPlaced (fanout between services)
    ↓
[email-queue]     → EmailConsumer (2 instances, competing)
[payment-queue]   → PaymentConsumer (5 instances, competing)
[warehouse-queue] → WarehouseConsumer (3 instances, competing)
```

Fanout between **service types**, competing consumers within **each service** for scale.

> MassTransit uses fanout exchange by default on `Publish()` — zero config needed.

---

## 🎯 Key Takeaway

> **Message queues trade latency for resilience** — decouple producers from consumers, buffer spikes, always define a DLQ strategy. Use `Channel<T>` for in-process async (fast, zero infra, but not durable). Use Kafka when you need replay/audit. Use RabbitMQ/Service Bus for task dispatch. Use MassTransit in .NET to avoid boilerplate and get retries, outbox, and sagas.

---

## Questions to Think About

1. In your current system, which synchronous service calls could be safely made async without impacting the user response?
2. You have `Channel<T>` processing critical data — what startup recovery logic would you add to handle a crash mid-processing?
3. You need 5 instances of PaymentService to all process different payments, but none should duplicate-process the same payment — competing consumer or fanout?
