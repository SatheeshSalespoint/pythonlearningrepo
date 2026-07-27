# Day 10 — Database Indexing & Query Optimisation

**Date:** 2026-07-28  
**Time:** 15 minutes  

---

## What is an Index?

An index is a **separate data structure** (usually a B-Tree) that lets the database find rows without scanning the full table.

```
Without index → Full Table Scan  O(n)   ← reads every row
With index    → B-Tree Lookup    O(log n) ← jumps straight to result
```

**The trade-off:**
> Indexes speed up **reads** but slow down **writes** — every INSERT/UPDATE/DELETE must also update the index.

---

## Types of Indexes

| Type | Description | When to Use |
|------|-------------|-------------|
| **Clustered** | Defines physical row order — 1 per table (PK by default) | Always exists on PK |
| **Non-Clustered** | Logical pointer to row — multiple allowed | Most common type |
| **Composite** | Multi-column index — column order matters | Filtering on multiple columns |
| **Covering** | Includes all queried columns — no table lookup needed | High-frequency hot queries |
| **Partial/Filtered** | Indexes only a subset of rows | Sparse data (e.g. `WHERE is_deleted = 0`) |

```sql
-- Composite index in MySQL
CREATE INDEX idx_tenant_status_date ON orders (tenant_id, status, created_at);

-- Covering index — includes SELECT columns to avoid table lookup
CREATE INDEX idx_cover ON orders (tenant_id, status) INCLUDE (total_amount);
```

```csharp
// EF Core equivalent
modelBuilder.Entity<Order>()
    .HasIndex(o => new { o.TenantId, o.Status, o.CreatedAt });
```

---

## The Golden Rules

### 1. Selectivity = Index Value

High selectivity (email, user_id) → great index  
Low selectivity (status: active/inactive) → weak index, optimizer often ignores it

> Rule: If a column has fewer than ~10 distinct values in a large table, don't index it alone.

### 2. Left-Prefix Rule for Composite Indexes

An index on `(A, B, C)` works for queries filtering on:

```
A           ✅
A + B       ✅
A + B + C   ✅
B           ❌ (skips A)
C           ❌ (skips A and B)
B + C       ❌ (skips A)
```

```sql
-- Index: (tenant_id, status, created_at)

SELECT * FROM orders WHERE tenant_id = 1 AND status = 'pending'     -- ✅ uses index
SELECT * FROM orders WHERE tenant_id = 1                             -- ✅ uses index
SELECT * FROM orders WHERE status = 'pending'                        -- ❌ skips index
```

### 3. Avoid Index-Breaking Patterns

```sql
-- ❌ Function on indexed column — index is ignored
WHERE YEAR(created_at) = 2025
WHERE LOWER(email) = 'test@example.com'

-- ✅ Rewrite as a range — index is used
WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01'
WHERE email = 'test@example.com'  -- store emails already lowercase

-- ❌ Leading wildcard — index ignored
WHERE name LIKE '%smith%'

-- ✅ Prefix search — index used
WHERE name LIKE 'smith%'

-- ❌ Implicit type conversion — index may be ignored
WHERE user_id = '12345'  -- user_id is INT, comparing to string

-- ✅ Match the column type
WHERE user_id = 12345
```

---

## Reading EXPLAIN / EXPLAIN ANALYZE (MySQL)

Always read the execution plan before tuning — never guess.

```sql
-- Basic explain
EXPLAIN SELECT * FROM orders WHERE tenant_id = 1 AND status = 'pending';

-- Full analysis with actual timings (MySQL 8.0+)
EXPLAIN ANALYZE SELECT * FROM orders WHERE tenant_id = 1 AND status = 'pending';

-- JSON format — shows cost estimates
EXPLAIN FORMAT=JSON SELECT ...;
```

### The `type` Column — Most Important Signal

```
system → const → eq_ref → ref → range → index → ALL
  best                                          worst
```

| type | Meaning | Good? |
|------|---------|-------|
| `const` | PK or unique lookup | ✅ Best possible |
| `eq_ref` | JOIN on unique/PK | ✅ |
| `ref` | Non-unique index match | ✅ |
| `range` | Index range scan (`BETWEEN`, `>`, `<`) | ✅ |
| `index` | Full index scan | ⚠️ |
| `ALL` | **Full table scan** | ❌ Fix this |

### Red Flags in the `Extra` Column

| Extra value | Problem | Fix |
|-------------|---------|-----|
| `Using filesort` | No index for ORDER BY | Add index on sort column |
| `Using temporary` | Temp table for GROUP BY / DISTINCT | Add composite index |
| `Using where` + `ALL` | Filter applied after full scan | Add index on WHERE columns |
| `Using index` | ✅ Covering index — no table lookup | Nothing to fix |

### Reading EXPLAIN ANALYZE Output

```
-> Sort: received_at DESC  (actual time=2.13..2.14 rows=59)
    -> Group aggregate  (actual time=1.65..2.03 rows=59)
        -> Nested loop left join  (actual time=1.6..1.95 rows=61)
            -> Index lookup on t  (actual time=0.785..0.797 rows=59)  ✅
            -> Index lookup on d  (actual time=0.018..0.019 rows=1 loops=59)  ✅
```

**Read bottom-up** — deepest indentation executes first.

```
actual time=1.66..2.09
         ↑      ↑
    first row  last row (total time)
```

> Use a visual tool instead of reading raw text — **explain.dalibo.com** (paste JSON output) or MySQL Workbench's built-in Visual Explain tab.

---

## System Design Angle — Indexes Aren't Enough at Scale

### 1. Read Replicas

Route heavy `SELECT` queries (reports, analytics) to read replicas. Never burn your primary DB on reads.

```
Primary DB  ← writes only (INSERT/UPDATE/DELETE)
    │
    ├── Read Replica 1  ← API reads
    └── Read Replica 2  ← reports / analytics
```

### 2. Pagination — Never `OFFSET` at Scale

```sql
-- ❌ OFFSET scans and discards all skipped rows — gets slower as page grows
SELECT * FROM orders ORDER BY id OFFSET 100000 LIMIT 20;
-- Page 1000 = scanning 100,000 rows just to skip them

-- ✅ Keyset / Cursor pagination — always fast regardless of page depth
SELECT * FROM orders WHERE id > :last_seen_id ORDER BY id LIMIT 20;
```

### 3. Denormalise for Hot Read Paths

If a query joins 5 tables and runs 10,000×/sec → materialise it.

```sql
-- ❌ Expensive at scale
SELECT u.name, COUNT(o.id), SUM(o.total)
FROM users u
JOIN orders o ON o.user_id = u.id
GROUP BY u.id;

-- ✅ Pre-computed column on users table, updated via event/trigger
SELECT name, order_count, order_total FROM users WHERE id = :id;
```

Or use a read model (CQRS — Day 15).

### 4. Connection Pooling

Every query needs a DB connection. Opening raw connections per request kills database performance.

```csharp
// EF Core — connection pooling is on by default
// Configure pool size for high-traffic apps
services.AddDbContext<AppDbContext>(options =>
    options.UseMySql(connectionString, serverVersion,
        o => o.CommandTimeout(30)),
    ServiceLifetime.Scoped
);

// For high concurrency — use PgBouncer (PostgreSQL) or ProxySQL (MySQL)
// between your app and database
```

### 5. Slow Query Log

Enable MySQL slow query log to catch issues in production:

```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- log queries > 1 second
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- Find worst offenders
SELECT query_time, sql_text
FROM mysql.slow_log
ORDER BY query_time DESC
LIMIT 10;
```

---

## Common Mistakes Senior Devs Make

| Mistake | Fix |
|---------|-----|
| Over-indexing write-heavy tables | Profile first — each index has a write cost |
| No index on foreign keys | Always index FK columns used in JOINs |
| Using `SELECT *` | Select only needed columns — enables covering indexes |
| `OFFSET` pagination on large tables | Switch to keyset/cursor pagination |
| Functions on WHERE columns | Rewrite as range or store pre-computed value |
| Missing composite index for multi-column WHERE | Column order: highest cardinality first |
| Never checking query plans | Run `EXPLAIN ANALYZE` on every new query before shipping |

---

## Quick Reference

```sql
-- Check existing indexes on a table
SHOW INDEX FROM orders;

-- Check table size and row count
SELECT table_name, table_rows, data_length, index_length
FROM information_schema.tables
WHERE table_schema = 'your_db' AND table_name = 'orders';

-- Find duplicate / redundant indexes
SELECT * FROM sys.schema_redundant_indexes;  -- MySQL sys schema

-- Force a specific index (debugging only)
SELECT * FROM orders FORCE INDEX (idx_tenant_date) WHERE tenant_id = 1;
```

---

## 🎯 Key Takeaway

> **Index the columns you filter and sort on; composite indexes follow the left-prefix rule; avoid functions on indexed columns. Use `EXPLAIN ANALYZE` (or a visual tool like explain.dalibo.com) to verify your plan. At scale, pair indexes with read replicas, cursor pagination instead of OFFSET, and connection pooling.**

---

## Questions to Think About

1. You have a table with 10 million orders. A query filters on `status = 'pending'` — there are only 3 possible status values. Why would MySQL ignore an index on `status`, and what should you do instead?
2. Your app uses `OFFSET 50000 LIMIT 20` for paginating an orders list. Page 1 is fast, page 2500 is slow. What's happening and how do you fix it?
3. You have a composite index on `(tenant_id, status, created_at)`. A query filters `WHERE status = 'pending' AND created_at > '2025-01-01'` with no `tenant_id` filter. Does it use the index? Why or why not?
