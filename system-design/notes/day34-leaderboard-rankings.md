# Day 34: Leaderboard / Rankings System (Sorted Sets, Skip Lists, Write Amplification)

**Date:** 2026-09-04  
**Duration:** ~50 mins  
**Status:** ✅ Complete  
**Difficulty:** Medium  
**Confidence Level:** 8/10 (strong engagement, self-corrected assumptions, challenged unsourced numbers)  
**Communication Level:** 8.5/10 (asked the right clarifying questions)

---

## The Challenge

Design the ranking system behind a SalesPoint dashboard:

- "Top 10 customers by revenue this month"
- "Sales rep rankings"
- "You're ranked #47 of 3,200 merchants"

Sounds trivial. The interesting part is that it is **write-heavy** — the inverse
of every system designed Days 20-33.

---

## Why the Obvious Approach Fails

```sql
SELECT customer_id, SUM(amount) AS total
FROM transactions
WHERE tenant_id = 42 AND created_at >= '2026-09-01'
GROUP BY customer_id
ORDER BY total DESC
LIMIT 10;
```

1. Scans every transaction for the month — 100M rows, seconds per query
2. Dashboard reloads constantly — that cost is paid repeatedly
3. "What is MY rank?" is worse — must rank *everyone* to locate one member

Root problem: **sorting on every read**, when the data barely changed.

---

## The Mechanism: Sorted Set (Z-set)

Order is maintained on **write**, so reads just navigate. Exact inverse of SQL.

```
ZADD  sales:2026-09  15000  acme
ZADD  sales:2026-09  22000  beta
ZADD  sales:2026-09   8000  gamma
ZADD  sales:2026-09  31000  delta
```

Always sorted internally:

```
rank 0 -> delta   31000
rank 1 -> beta    22000
rank 2 -> acme    15000
rank 3 -> gamma    8000
```

### Operations and true costs

```
ZSCORE     O(1)          hash map lookup           "what is my score"
ZADD       O(log N)      skip list insert
ZINCRBY    O(log N)      hash lookup + reposition
ZREVRANK   O(log N)      skip list walk, sum spans "what is my position"
ZREVRANGE  O(log N + M)  locate start, walk M nodes
ZCARD      O(1)          counter on the set
```

**Nothing ever sorts.** Order is paid for on write.

### Command naming

Redis prefixes by data type: (none)=String, `L`=List, `S`=Set, `H`=Hash, `Z`=Sorted Set.
`S` was taken by Set, so sorted set became **Z-set**.

```
Z + [REV] + operation

ZCARD    = Z + CARDinality (math term for set size)
ZINCRBY  = Z + INCRement BY
ZREVRANK = Z + REVerse + RANK
```

**Gotcha:** sets store **ascending**. A leaderboard almost always needs `REV`.
Omit it and you silently render the *worst* performers.

```
ZRANGE    sales 0 1  ->  [gamma 8000,  acme 15000]   <- WORST two
ZREVRANGE sales 0 1  ->  [delta 31000, beta 22000]   <- BEST two  OK
```

---

## Internals: Skip List + Hash Map

Redis keeps **two structures** for one sorted set, sharing one copy of each member string.

```csharp
public class SortedSet
{
    private readonly Dictionary<string, double> _scores = new();  // O(1) member -> score
    private readonly SkipList _skipList = new();                  // O(log N) order & rank
}

public class SkipListNode
{
    public string Member;          // 8 bytes (reference)
    public double Score;           // 8 bytes
    public SkipListNode Backward;  // 8 bytes
    public Level[] Levels;         // 16 bytes per level
}

public struct Level
{
    public SkipListNode Forward;   // 8 bytes
    public long Span;              // 8 bytes  <- makes ZRANK O(log N)
}
```

### Express lanes

```
L3:  HEAD ------------------------------------------------> NIL
L2:  HEAD ---------------------> m4 -----------------------> NIL
L1:  HEAD -----------> m2 -----> m4 ---------> m6 ---------> NIL
L0:  HEAD -> m1 -----> m2 -> m3 -> m4 -> m5 -> m6 -> m7 -> m8 -> NIL
```

Search m7: start high, advance while next < target, drop a level on overshoot.
4 moves instead of 7.

```
N = 8          linked list 8 steps        skip list ~3
N = 1,000      linked list 1,000          skip list ~10
N = 1,000,000  linked list 1,000,000      skip list ~20
```

### Spans — why ZRANK is O(log N)

Every pointer stores how many base-level nodes it jumps.

```csharp
public long GetRank(string member)
{
    double score = _scores[member];           // O(1)
    long rank = 0;
    var node = _head;

    for (int level = _maxLevel - 1; level >= 0; level--)
    {
        while (node.Levels[level].Forward != null &&
               node.Levels[level].Forward.Score <= score)
        {
            rank += node.Levels[level].Span;  // accumulate while searching
            node  = node.Levels[level].Forward;
        }
    }
    return rank - 1;
}
```

**Position is never stored.** It is accumulated along the search path — hence
`O(log N)`, not `O(1)` and not `O(N)`.

### No rebalancing — a coin flip

```csharp
private int RandomLevel()
{
    int level = 1;
    while (_random.NextDouble() < 0.25 && level < MaxLevel)
        level++;
    return level;
}
```

That is the entire balancing algorithm. Compare to red-black tree rotations.
Balance emerges statistically: ~75% stay at L1, ~19% reach L2, ~5% reach L3.

**Why Redis chose skip list over a balanced tree:**
1. `ZRANGE` is a natural L0 walk (a tree needs in-order traversal with a stack)
2. No rotation logic to write or get wrong
3. Localized pointer updates — simpler concurrency

### Why both structures

```csharp
public async Task IncrementAsync(string member, double delta)
{
    _scores.TryGetValue(member, out double old);  // 1. O(1) — without dict this is O(N)
    double updated = old + delta;
    _skipList.Delete(member, old);                // 2. O(log N)
    _skipList.Insert(member, updated);            // 3. O(log N)
    _scores[member] = updated;                    // 4. O(1)
}
```

---

## StackExchange.Redis (what SalesPoint would actually call)

```csharp
IDatabase db = redis.GetDatabase();
const string key = "lb:tenant42:revenue:month:2026-09";

await db.SortedSetAddAsync(key, "cust_88", 15000);              // ZADD
await db.SortedSetIncrementAsync(key, "cust_88", 5000);         // ZINCRBY

SortedSetEntry[] top10 = await db.SortedSetRangeByRankWithScoresAsync(
    key, start: 0, stop: 9, order: Order.Descending);           // ZREVRANGE

long? rank  = await db.SortedSetRankAsync(
    key, "cust_88", Order.Descending);                          // ZREVRANK
long  total = await db.SortedSetLengthAsync(key);               // ZCARD
```

**Warning:** `Order.Descending` is **not** the default.

---

## Memory

### Per member (~100 bytes)

```
skip list node    ~55   (Member ptr 8 + Score 8 + Backward 8 + levels ~21 + malloc ~10)
SDS string        ~20   (shared between skiplist node and dict entry — stored ONCE)
dictEntry+bucket  ~42
------------------------
                 ~117   -> working figure ~100 bytes/member
```

**Why 8 bytes everywhere:** 64-bit CPU -> addresses are 64 bits -> every pointer/reference
is 8 bytes regardless of what it points at. `double` is 8 bytes by IEEE 754
(1 sign + 11 exponent + 52 mantissa). `long` is 8. On 32-bit, pointers halve to 4.

**Value vs reference:** `Score` is a value type — the 8 bytes *are* the number.
`Member` is a reference — the 8 bytes are an *address*; characters live elsewhere.

### Listpack optimization

```
zset-max-listpack-entries  128   (default)
zset-max-listpack-value    64

<= 128 members  -> flat listpack  ~25 bytes/member   (4x cheaper)
>  128 members  -> skiplist+hash ~100 bytes/member
```

### Memory is per DISTINCT MEMBER, not per write

```csharp
await db.SortedSetIncrementAsync(key, "cust_88", 500);  // exists -> 0 new bytes
await db.SortedSetIncrementAsync(key, "cust_99", 500);  // new    -> +100 bytes
```

30,000 writes/sec add almost **zero** memory — the same customers transact repeatedly,
scores climb, member count does not. A customer with 10,000 payments costs the same
100 bytes as one with a single payment.

---

## Scale Estimation

### The dimension explosion (the trap)

It is never ONE leaderboard:

```
    100,000 tenants
  x       4 time windows (day, week, month, all-time)
  x       3 metrics (revenue, txn count, customers)
  --------------------------------------------------
  1,200,000 leaderboards
```

### Memory — board size varies by window

First pass applied 500 members to *every* board -> 60 GB. Wrong: a **daily** board
only contains customers who transacted *today*.

```
Per tenant, per metric:
  daily      20 members x 100 bytes =    2,000
  weekly     80 members x 100 bytes =    8,000
  monthly   200 members x 100 bytes =   20,000
  all-time  500 members x 100 bytes =   50,000
  ---------------------------------------------
                                        80,000 bytes = 80 KB

  80,000 x 3 metrics          =    240,000 bytes = 240 KB per tenant
  240,000 x 100,000 tenants   = 24,000,000,000 bytes = 24 GB
```

With listpack on the small daily/weekly boards -> **~22 GB**.

### Writes — amplification

```csharp
public async Task RecordTransactionAsync(Transaction txn)
{
    var windows = new[] { "day:2026-09-04", "week:2026-W36", "month:2026-09", "all" };
    var metrics = new[] { "revenue", "txncount", "customers" };

    foreach (var window in windows)
    foreach (var metric in metrics)
        await db.SortedSetIncrementAsync(
            $"lb:{txn.TenantId}:{metric}:{window}", txn.CustomerId, txn.Amount);
    // 12 Redis round trips for ONE payment
}
```

```
50,000 req/sec x 5% transactions =  2,500 transactions/sec
 2,500 x 12 boards               = 30,000 ZINCRBY/sec
```

### Reads — driven by DASHBOARD VIEWS, not transactions

Key correction. A payment arriving does not cause anyone to open a leaderboard.

```
WRITE trigger: a customer pays money
READ  trigger: a merchant opens the dashboard screen
```

```
100,000 users x 100 views/day = 10,000,000 views/day
10,000,000 / 86,400           =        115 views/sec
115 x 12 peak                 =      1,380 views/sec
1,380 x 2 ops (ZREVRANGE + ZREVRANK) = 2,760 read ops/sec
```

### THE FINDING: leaderboards are WRITE-heavy

```
WRITES  30,000 ops/sec  ################################
READS    2,760 ops/sec  ###

ratio ~ 11 : 1  WRITE-heavy
```

**This inverts Days 20-33:**

| Day | System | Ratio | Solved by |
|---|---|---|---|
| 20 | URL Shortener | 10:1 read | cache + read replicas |
| 23 | Instagram Feed | 5:1 read | hybrid fanout + cache |
| 24 | Autocomplete | ~1000:1 read | Trie + 3-tier cache |
| 28 | Twitter Feed | high read | pull-on-demand |
| 33 | Search Engine | high read | inverted index + cache |
| **34** | **Leaderboard** | **11:1 WRITE** | **cache does nothing** |

The whole toolkit — caching, read replicas, CDN, precomputation — exists to make
**reads** cheap. None of it applies. Reads run at 3% of ceiling.

```
   2,500 transactions/sec        <- business volume, cannot reduce
 x    12 boards per transaction  <- self-inflicted design choice
```

---

## Assumption Sensitivity — the day's sharpest lesson

```
At 20% transaction rate:  120,000 writes/sec  -> OVER ~100K ceiling  FAIL, must shard
At  5% transaction rate:   30,000 writes/sec  -> 30% utilization     OK, one instance
```

**A number picked in thirty seconds flipped the architecture verdict.** Same lesson
as Day 33, where a 100x error moved "one server" to "distributed with coordinator."

State assumptions out loud so an interviewer can correct them *before* you design
the wrong system.

---

## Verdict at these assumptions

```
Throughput  30,000 writes/sec  vs ~100,000 ceiling   OK
Reads        2,760 ops/sec     vs ~100,000 ceiling   OK
Memory          24 GB          manageable            OK

-> No hard bottleneck. The naive design holds.
```

Worth stating in an interview, then naming what *would* break it:
10x the tenants, 20% transaction rate, or enterprise tenants with 50,000 customers.

**Levers if it did break:** cut the x12 (do all 4 windows need real-time updates?),
pipeline the 12 round trips into one, buffer-and-flush every N seconds, shard by
tenant hash (Day 25 pattern), or lazily create only boards someone actually opens.

---

## Do Not Trust Unsourced Numbers

Challenged the "~100K ops/sec Redis ceiling." Correct instinct — it is a commonly
reported figure, not a specification. Real value swings on command complexity,
pipelining, network RTT, payload size, CPU.

**Fundamental constraint: Redis executes commands single-threaded — one CPU core.**
A 32-core box does not make one instance faster. Scale = more instances, not more
cores (validates the Day 25 sharding answer). One slow `O(N)` command blocks all clients.

**Measure instead of estimating:**

```bash
redis-benchmark -h host -p 6379 -c 50 -P 10 -n 1000000 \
  zincrby leaderboard:test 1 member:__rand_int__
# preload ~500 members first — ZINCRBY is O(log N), an empty set flatters results

redis-cli INFO stats | grep instantaneous_ops_per_sec
redis-cli INFO memory
redis-cli MEMORY USAGE <key>
redis-cli --bigkeys
redis-cli --latency
```

```csharp
var server = redis.GetServer("host", 6379);
var stats  = await server.InfoAsync("stats");   // instantaneous_ops_per_sec
```

**When precision matters:**
```
Need 30,000, ceiling 50,000-200,000  -> fine across whole range, do not measure
Need 95,000, ceiling 50,000-200,000  -> design flips, MEASURE FIRST
```

Order of magnitude decides architecture. Precision comes from measurement.

---

## Interview Technique: State, Do Not Ask

| **Ask them** (only they know) | **Bring yourself** (craft) |
|---|---|
| How many tenants? | Redis ~ 100K ops/sec/instance |
| Peak transaction volume? | Redis is single-threaded |
| Customers per tenant? | `ZINCRBY` is O(log N) |
| Which time windows are actually used? | ~100 bytes/member |
| Real-time rank, or is 1 min stale OK? | Skip list internals |
| Multi-region? | Sharding patterns |

```
BAD:  "What is Redis's throughput ceiling?"     <- signals you have never sized Redis

GOOD: "I am working with ~100K ops/sec per instance for O(log N) commands — flag me
       if your numbers differ. My requirement is 30K, so ~3x headroom."
```

Same protection, without signalling ignorance. **Ask about their domain, bring your craft.**

Strongest question available on this problem:
> *"Do users actually look at all four time windows, or mostly monthly? That is a
> 4x difference in write amplification."*

Legitimate environment question:
> *"Do you already run Redis in production? What instance sizes — I would rather size
> against what you have than assume."*

---

## Corrections Made During Session

1. **"log N for sorting"** -> nothing sorts; `log N` locates the start position
2. **`ZREVRANK` is O(1)** -> it is `O(log N)`; `ZSCORE` is the O(1) one
   (score = hash map; *position* must be counted via spans)
3. **Members = "top 10"** -> members = the full ranked population (500 customers);
   top 10 is only the read window. Set holds all 500 because ranks change,
   `ZREVRANK` needs everyone present, and scores accumulate all month
4. **"one write = 100 bytes"** -> memory is per *distinct member*; repeat `ZINCRBY`
   on an existing member costs zero new bytes
5. **Reads driven by transactions** -> reads driven by *dashboard views*; entirely
   independent event streams
6. **500 members on every board** -> daily boards hold only today's actives (~20)

---

## Assessment

**Landed:**
- Sorted set mechanism and true operation costs
- Skip list: express lanes, spans, probabilistic levels, why Redis chose it
- Dual structure (hash + skiplist) and why both are needed
- Dimension explosion as the real scale driver
- Write-heavy discovery — inverts the entire Days 20-33 toolkit
- Assumption sensitivity flipping the architecture verdict
- Challenging unsourced numbers (senior behaviour)

**Arithmetic:** clean today — zeros written out, `100,000 x 100 = 10,000,000` correct.
Marked improvement over Day 33.

**Confidence: 8/10.** Several conceptual errors, all self-corrected on explanation.
Pushing back on the "magic number" was the strongest moment of the session.

---

## Next: Day 35 — Checkpoint Assessment

Review Days 22-34, assess readiness for Phase 3 (Hard systems, Days 36-45).
Day 33 (Search Engine) still open — ranking, sharding, and Q2/Q3/Q4 outstanding.
