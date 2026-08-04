# Day 15 — CQRS Pattern

**Date:** 2026-08-04  
**Time:** 15 minutes

---

## The Core Idea

**One model for reads, a different model for writes.**

> "A method should either *change state* (Command) or *return data* (Query) — never both." — Bertrand Meyer (CQS principle)

CQRS takes this further: **separate the entire stack** — different handlers, different models, optionally different databases.

```
TRADITIONAL (CRUD)
   UI → Single Model → Single DB
       (reads and writes share same model/table)

CQRS
   UI → Command Handler → Write DB (domain model)
   UI → Query Handler  → Read DB  (projections / joins / views)
```

---

## Commands vs Queries

| | Command | Query |
|---|---|---|
| **Purpose** | Change state | Return data |
| **Examples** | `PlaceOrder`, `CreateTransaction` | `GetOrderSummary`, `ListProducts` |
| **Returns** | ID / outcome / void | DTO / projection |
| **Side effects** | Yes | None — ever |

---

## Write Side — The Domain Model

The write side owns **business invariants**. It is intentionally NOT optimised for reads.

```csharp
public class Order
{
    private readonly List<OrderLine> _lines = new();
    public Guid Id { get; private set; }
    public OrderStatus Status { get; private set; }

    // Enforces business rule — not a data concern
    public void AddLine(Product product, int quantity)
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Cannot modify a confirmed order.");

        _lines.Add(new OrderLine(product, quantity));
    }
}
```

**Key rule:** Command handlers return only what the client **could not have known before the request.**

```csharp
public async Task<Guid> HandleAsync(CreateOrderCommand cmd, CancellationToken ct)
{
    var order = Order.Create(cmd.CustomerId, cmd.Items);
    await _db.Orders.AddAsync(order, ct);
    await _db.SaveChangesAsync(ct);
    return order.Id;  // client already has everything else it sent
}
```

### When to return more than just an ID

Only return more than an ID when the server produces **new information** the client never had:

```csharp
// Payment — gateway response is new information ✅
return new CreateTransactionResult(
    transaction.Id,           // server-generated
    gatewayResponse.Status,   // gateway decision — client didn't know
    gatewayResponse.AuthCode  // gateway response — client didn't know
);

// Echoing back what the client sent ❌
return new CreateTransactionResult(
    transaction.Id,
    cmd.Amount,     // client already knows this
    cmd.Currency    // client already knows this
);
```

> **Rule:** Return only what the client could NOT have known before the request.

---

## Read Side — Query Handlers

Query handlers read data and return it. No business logic, no state mutation.

```csharp
public async Task<OrderSummaryDto> HandleAsync(GetOrderQuery q, CancellationToken ct)
{
    // Joins are fine on the read side
    return await _db.QuerySingleAsync<OrderSummaryDto>(
        @"SELECT o.*, c.full_name, c.email
          FROM orders o
          JOIN customers c ON o.customer_id = c.id
          WHERE o.id = @id",
        new { id = q.OrderId });
}
```

### Joins vs Projections — It's a Performance Decision, Not a CQRS Rule

| Approach | When to Use |
|---|---|
| **Joins / views** | Normal traffic, simple queries, same DB |
| **Pre-computed projection tables** | High-traffic, performance-critical reads |
| **Read replica** | When read load outgrows write DB capacity |
| **Separate read store (Redis, Elasticsearch)** | Only at significant scale |

> **CQRS forbids loading domain aggregates for read purposes and executing business logic in queries. It does NOT forbid joins.**

```csharp
// ❌ Violates CQRS — loading write model for reading
var order = await _db.Orders.Include(o => o.Lines).FirstOrDefaultAsync(o => o.Id == id);
order.CalculateTotal(); // business logic in a query handler

// ✅ Correct — purpose-built query, no domain logic
var dto = await _db.QuerySingleAsync<OrderSummaryDto>("SELECT ... JOIN ...", new { id });
```

---

## Scaling Pattern — Same DB to Read Replica

```
Small app (your current state)        At scale
──────────────────────────────        ──────────────────────────────
Command Handler ──▶ Primary DB        Command Handler ──▶ Primary DB
Query Handler   ──▶ Primary DB        Query Handler   ──▶ Read Replica
                                                           (auto-synced)
```

No code change needed other than connection string routing. This is the natural CQRS scaling path.

---

## Implementing CQRS Without MediatR

MediatR went commercial (v12+, 2024). You don't need it — CQRS is a pattern, not a library.

### Define the Interfaces

```csharp
public interface ICommandHandler<TCommand, TResult>
{
    Task<TResult> HandleAsync(TCommand command, CancellationToken ct);
}

public interface IQueryHandler<TQuery, TResult>
{
    Task<TResult> HandleAsync(TQuery query, CancellationToken ct);
}
```

### Register in DI

```csharp
builder.Services.AddScoped<ICommandHandler<CreateOrderCommand, Guid>, CreateOrderHandler>();
builder.Services.AddScoped<IQueryHandler<GetOrderQuery, OrderSummaryDto>, GetOrderHandler>();
```

### Use in Controller

```csharp
[ApiController]
[Route("orders")]
public class OrdersController : ControllerBase
{
    private readonly ICommandHandler<CreateOrderCommand, Guid> _createOrder;
    private readonly IQueryHandler<GetOrderQuery, OrderSummaryDto> _getOrder;

    [HttpPost]
    public async Task<IActionResult> Create(CreateOrderCommand cmd, CancellationToken ct)
        => Ok(await _createOrder.HandleAsync(cmd, ct));

    [HttpGet("{id}")]
    public async Task<IActionResult> Get(Guid id, CancellationToken ct)
        => Ok(await _getOrder.HandleAsync(new GetOrderQuery(id), ct));
}
```

### Why MediatR Was Popular (Before It Went Commercial)

| Problem | Pure DI | MediatR |
|---|---|---|
| Growing handler dependencies | Constructor bloat per controller | Single `IMediator` forever |
| Cross-cutting concerns (logging, validation) | Manual per handler | Pipeline behaviours |
| Handler auto-discovery | Manual DI registration | Assembly scanning |

**Free alternatives:** Wolverine (open-source, also handles messaging), Brighter, or pure DI as above.

---

## The CQRS Spectrum — Don't Over-Engineer

```
Basic CQRS  ← Correct starting point
(same DB, joins ok, separate command/query handlers)

      ↓ only when read/write loads diverge significantly

Advanced CQRS
(read replica, pre-computed projections, event-driven sync)

      ↓ only when paired with Event Sourcing

CQRS + Event Sourcing
(event store, full projection rebuild from event history)
```

> Do not jump to event-driven projections unless you've outgrown the simpler approach.

---

## When to Use CQRS

| ✅ Good Fit | ❌ Skip It |
|---|---|
| Read/write loads differ significantly | Simple CRUD apps |
| Complex domain logic (DDD fit) | Small teams, early stage |
| Independent scaling needed | Low traffic, single service |
| Pairs with Event Sourcing (Day 16) | Added complexity not justified |

---

## Connection to Previous Days

| Topic | How CQRS Relates |
|-------|-----------------|
| **Day 7 — Message Queues** | Advanced CQRS uses events to sync read models asynchronously |
| **Day 10 — DB Indexing** | Read models and projections are where index optimisation matters most |
| **Day 11 — Microservices** | CQRS is a natural fit per microservice for separating read/write concerns |
| **Day 14 — EDA** | Event-driven projection updates are the bridge between EDA and advanced CQRS |
| **Day 16 — Event Sourcing** | CQRS pairs naturally with Event Sourcing — projections rebuilt from event log |

---

## 🎯 Key Takeaway

> **CQRS = separate command handlers that mutate state from query handlers that return data.** Commands return only what the client couldn't have known (usually just the ID). Query handlers can use joins, views, or raw SQL — whatever is fastest. Start with the same DB; move to a read replica when read load demands it. MediatR was popular because it solved constructor bloat at scale — not because CQRS required it. You don't need it; pure DI interfaces work perfectly. Don't layer event-driven projections until you've outgrown the simple approach.
