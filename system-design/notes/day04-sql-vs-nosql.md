# Day 4 — Databases: SQL vs NoSQL

**Date:** 2026-07-16  
**Time:** 15 minutes  

---

## The Core Difference

**SQL** — data has a fixed structure (schema), stored in rows & columns, relationships enforced.  
**NoSQL** — flexible structure, many shapes (documents, key-value, graphs), optimised for scale.

```
SQL:     Table → Row → Column  (strict, typed, relational)
NoSQL:   Collection → Document (flexible, schema-free)
```

---

## SQL — When to Use It

| Feature | Detail |
|---|---|
| **Structure** | Fixed schema — every row has the same columns |
| **Relationships** | Foreign keys, JOINs across tables |
| **Transactions** | ACID — Atomicity, Consistency, Isolation, Durability |
| **Best for** | Financial data, orders, user accounts, anything needing integrity |

```sql
-- Relationships enforced at DB level
SELECT orders.id, users.name
FROM orders
JOIN users ON orders.user_id = users.id
WHERE orders.status = 'pending'
```

> Your C# background: **SQL Server / EF Core** = classic SQL. You already know this model.

---

## NoSQL — 4 Types

| Type | Example | Use Case |
|---|---|---|
| **Document** | MongoDB, Cosmos DB | JSON objects — user profiles, product catalogs |
| **Key-Value** | Redis, DynamoDB | Session store, cache, leaderboards |
| **Column-family** | Cassandra | Time-series data, IoT events, analytics |
| **Graph** | Neo4j | Social networks, fraud detection, recommendations |

---

## The Trade-off Table

| | SQL | NoSQL |
|---|---|---|
| Schema | Fixed (migrations needed) | Flexible (add fields anytime) |
| Relationships | Strong (JOINs, FK) | Weak (embed or reference manually) |
| Transactions | ✅ Full ACID | ⚠️ Usually eventual consistency |
| Horizontal scale | ❌ Hard (sharding is complex) | ✅ Built-in (designed for scale) |
| Query power | ✅ Rich SQL queries | ⚠️ Limited (no ad-hoc JOINs) |
| Best fit | Structured, relational data | High volume, flexible, fast writes |

---

## ⚠️ The Biggest Mistake

> Picking NoSQL because it "sounds modern" — then realising you need transactions.

Example: **An e-commerce order** must:
1. Deduct stock
2. Create the order
3. Charge the customer

All 3 must succeed or all 3 must roll back. That's **ACID**. Use SQL.

---

## Real-World Hybrid Pattern

Most large systems use **both**:

```
User Profile ──────→ PostgreSQL (relational, ACID)
User Activity Feed ─→ Cassandra  (high write volume, time-ordered)
Session Tokens ────→ Redis       (key-value, fast expiry)
Product Catalogue ─→ MongoDB     (flexible schema, nested data)
```

Don't pick one — pick the right tool per problem.

---

## C# / Azure Context

| Need | Tool |
|---|---|
| Relational + ACID | **Azure SQL** / SQL Server + EF Core |
| Document store | **Azure Cosmos DB** (MongoDB-compatible API) |
| Key-value / cache | **Azure Cache for Redis** |
| Globally distributed | **Cosmos DB** (multi-region writes) |

---

## 🎯 Key Rule

> **If your data has relationships and needs consistency — use SQL.**  
> **If your data is high-volume, flexible, or globally distributed — use NoSQL.**  
> When in doubt: start with SQL. It's easier to migrate to NoSQL than to recover from missing transactions.

---

## Questions to think about

1. Your current C# API — does it use SQL Server? What would break if you switched to a document store?
2. Think of one piece of data in your app that could be NoSQL — what makes it a good candidate?
3. If you had to store 1 million user events per day, would you use SQL or Cassandra? Why?
