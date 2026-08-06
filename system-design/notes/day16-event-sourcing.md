# Day 16 — Event Sourcing

**Date:** 2026-08-06  
**Time:** 15 minutes

---

## The Core Idea

**Instead of storing current state, store a log of every event that led to that state.**

> "Current state = replaying all past events in order."

```
TRADITIONAL (CRUD)
   INSERT order → UPDATE order SET status='shipped' → UPDATE order SET status='delivered'
   You only see: status = 'delivered'  (history is lost)

EVENT SOURCING
   OrderCreated → ItemAdded → PaymentReceived → OrderShipped → OrderDelivered
   State is derived by replaying events — history is the data
```

---

## Traditional DB vs Event Sourcing

| Traditional | Event Sourcing |
|---|---|
| `UPDATE orders SET status='shipped'` | Append `OrderShipped { id, timestamp }` |
| You see current state only | Full history always available |
| Hard to answer "what happened?" | Audit is free — it IS the data |
| Overwrites previous values | Append-only — nothing ever deleted |

---

## Key Concepts

### 1. Event Store
An **append-only log** of all events. Never updated, never deleted.

Options:
- **EventStoreDB** — purpose-built (streams, subscriptions built-in)
- **Kafka** — easy to replay, built-in partitioning
- **SQL table** — simple, works well for most systems

```sql
CREATE TABLE pos_events (
    id              BIGINT IDENTITY PRIMARY KEY,
    aggregate_id    UNIQUEIDENTIFIER NOT NULL,   -- e.g. SaleId, ShiftId
    aggregate_type  NVARCHAR(50)     NOT NULL,   -- 'Sale', 'Shift', 'Inventory'
    event_type      NVARCHAR(100)    NOT NULL,   -- 'SaleCompleted', 'RefundIssued'

    -- Filter keys — anything you query BY goes here as a column
    store_id        UNIQUEIDENTIFIER NOT NULL,
    cashier_id      UNIQUEIDENTIFIER NOT NULL,
    terminal_id     UNIQUEIDENTIFIER,

    payload         NVARCHAR(MAX)    NOT NULL,   -- JSON event data
    occurred_at     DATETIME2        NOT NULL
);
```

> **Rule:** Anything you filter or query by → make it a column, not buried in JSON payload.

---

### 2. Aggregate
An entity whose current state is **rebuilt by replaying its events in order**.

```
Replay: OrderCreated → ItemAdded → PaymentReceived → OrderShipped
Result: Order { status = Shipped, items = [...], total = 43.50 }
```

```csharp
// Events are immutable records
public record OrderShipped(Guid OrderId, DateTime ShippedAt);

// Aggregate replays events to rebuild state
public class Order
{
    public OrderStatus Status { get; private set; }
    public void Apply(OrderShipped e) => Status = OrderStatus.Shipped;
}
```

---

### 3. Snapshot
A **periodic checkpoint** to avoid replaying thousands of events every time.

```
Without snapshot: Replay 10,000 events every time you load an Order ❌
With snapshot:    Load snapshot (event #9950) + replay last 50 events ✅
```

```sql
CREATE TABLE pos_snapshots (
    aggregate_id   UNIQUEIDENTIFIER,
    snapshot_data  NVARCHAR(MAX),   -- current state as JSON
    last_event_id  BIGINT,          -- replay only events AFTER this
    created_at     DATETIME2
);
```

Rule of thumb: create a snapshot every 50–100 events per aggregate.

---

### 4. Projection
A **read-optimised view** built by listening to events. This is the bridge to CQRS.

```
Event Store → Projection Builder → Read DB (sales_summary, cashier_report, etc.)
```

```sql
-- Projection: updated whenever SaleCompleted event fires
CREATE TABLE sales_summary (
    store_id     UNIQUEIDENTIFIER,
    sale_date    DATE,
    total_sales  DECIMAL(10,2),
    tx_count     INT
);
```

> Never run aggregate queries (SUM, COUNT) directly on the event store — use projections for reports.

---

## Replaying Events from SQL

Replay = `SELECT * WHERE aggregate_id = @id ORDER BY id` → apply each row to rebuild state.

```sql
-- Replay a single sale
SELECT * FROM pos_events
WHERE aggregate_id = 'sale-001'
ORDER BY id;
```

Unlike Kafka (which has built-in replay), SQL replay is manual — but simple and effective.

---

## POS System Example

### Events to Capture
```
SaleStarted, ItemAdded, DiscountApplied,
SaleCompleted, SaleVoided, RefundIssued,
CashDrawerOpened, ShiftStarted, ShiftClosed,
PriceOverridden   ← audit gold for managers
```

### Sample Data

| id | aggregate_id | aggregate_type | event_type | store_id | cashier_id | payload | occurred_at |
|---|---|---|---|---|---|---|---|
| 1 | sale-001 | Sale | SaleStarted | store-A | john | `{"terminal":"T1"}` | 10:00:01 |
| 2 | sale-001 | Sale | ItemAdded | store-A | john | `{"item":"Coke","price":2.50}` | 10:00:05 |
| 3 | sale-001 | Sale | DiscountApplied | store-A | john | `{"discount":10}` | 10:00:10 |
| 4 | sale-001 | Sale | SaleCompleted | store-A | john | `{"total":3.87}` | 10:00:12 |
| 5 | shift-001 | Shift | ShiftStarted | store-A | john | `{"float":200.00}` | 09:00:00 |
| 6 | inv-001 | Inventory | StockAdjusted | store-A | sue | `{"item":"Coke","qty":-24}` | 09:30:00 |
| 7 | sale-001 | Sale | RefundIssued | store-A | sue | `{"amount":3.87}` | 10:15:00 |

### Query Examples

```sql
-- Replay one sale
SELECT * FROM pos_events
WHERE aggregate_id = 'sale-001'
ORDER BY id;

-- All refunds in Store-A today
SELECT * FROM pos_events
WHERE store_id = 'store-A'
AND event_type = 'RefundIssued'
AND occurred_at >= CAST(GETDATE() AS DATE);

-- Everything cashier John did this shift
SELECT * FROM pos_events
WHERE cashier_id = 'cashier-john'
AND occurred_at BETWEEN '09:00' AND '18:00'
ORDER BY occurred_at;

-- Only inventory events
SELECT * FROM pos_events
WHERE aggregate_type = 'Inventory'
AND store_id = 'store-A';
```

---

## One Table — Not Many Tables

**Use `aggregate_type` as separator, not separate tables.**

| ❌ Separate Tables | ✅ One Table + aggregate_type |
|---|---|
| "Show everything cashier X did" → JOIN 5 tables | Single query with `WHERE cashier_id = @id` |
| Add new event type → new table | Just insert with new `event_type` value |
| Replay a full shift → scattered data | All events in one place, ordered by id |

Only use separate databases (not tables) if domains are completely unrelated — e.g. POS events vs HR/payroll.

---

## Managing a Large Event Table

The event store grows fast. A busy POS store = ~5,000 events/day = 1.8M rows/year.

### 4 Strategies

**1. Partitioning**
```sql
-- Partition by month — queries scan only relevant partition
PARTITION BY RANGE (occurred_at)
```

**2. Archiving**
```
pos_events          ← hot  (last 90 days, fully indexed)
pos_events_archive  ← cold (older, minimal indexes, cheap storage)
```

**3. Projections — Never query events for reports**
```
❌ SUM() on pos_events for daily report
✅ SUM() on sales_summary projection
```

**4. Snapshots — Avoid full replay on large aggregates**
```
Load snapshot + replay last 50 events
instead of replaying 10,000 events
```

### Recommended Indexes
```sql
INDEX ix_store     (store_id, occurred_at)
INDEX ix_cashier   (cashier_id, occurred_at)
INDEX ix_aggregate (aggregate_id)
INDEX ix_type      (aggregate_type, event_type, occurred_at)
```

---

## Event Sourcing vs Application Logs

| App Logs | Event Sourcing |
|---|---|
| For **developers** (debugging, monitoring) | For **the business** (audit, state) |
| Unstructured text (`"Payment failed at line 42"`) | Structured, typed events (`PaymentFailed { amount, reason }`) |
| Throwaway — rotated/deleted | **Source of truth** — never deleted |
| Cannot rebuild state | State is **derived** by replaying them |

> Logs are noise. Events are official business facts.

---

## Real Uses Beyond Auditing

| Use Case | How Event Sourcing Helps |
|---|---|
| **Undo / Compensate** | Replay shows exactly what fired — compensate precisely |
| **Time travel** | "What was the order state last Tuesday 3pm?" — replay up to that timestamp |
| **Bug fix retroactively** | Replay all events with fixed logic → exact refund amounts |
| **New feature from old data** | Create a new projection from existing events — data was always there |

---

## When to Use / Avoid

| ✅ Use | ❌ Avoid |
|---|---|
| Audit required (finance, POS, health) | Simple CRUD apps |
| Undo / redo needed | Team unfamiliar with the pattern |
| Temporal queries needed | Storage cost is a concern |
| Pairs with CQRS for scalable reads | Low-traffic, early-stage apps |

---

## Connection to Previous Days

| Topic | How Event Sourcing Relates |
|---|---|
| **Day 7 — Message Queues** | Kafka is a natural event store — built-in replay and partitioning |
| **Day 14 — EDA** | Events are the same concept — EDA is about routing them; ES is about storing them as truth |
| **Day 15 — CQRS** | Commands emit events to event store; queries read projections — natural pairing |

---

## Architecture Flow (CQRS + Event Sourcing)

```
Command → [Event Store] → Projection Builder → [Read DB] → Query
                       → Kafka (optional)    → Other consumers
```

- **Commands** write events (append-only)
- **Queries** read projections (read-optimised)
- **No new method type** needed — events slot into existing command handlers

---

## 🎯 Key Takeaway

> **Event Sourcing = append-only facts. State is derived, never stored directly.** Use `aggregate_type` as separator — one table, not many. Filter keys (store_id, cashier_id) belong as columns, not in JSON. Never query the event store for reports — build projections. Snapshots fix replay performance. Archive old events for cost control. Use when history IS the business requirement — perfect for POS, payments, and booking systems.
