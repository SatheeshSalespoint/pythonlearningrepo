# Day 37: Search Engine — Architecture Complete (closes Day 33)

**Date:** 2026-09-10
**Duration:** ~60 mins
**Status:** ✅ Complete — Day 33 now closed
**Phase:** 2.5 Bridge (Days 36–40)
**Difficulty:** Medium → Hard (information retrieval, no prior anchor)
**Confidence:** 7/10 (up from 5/10 on Day 33)

---

## What This Day Closed

Day 33 (2026-09-03) stopped after the inverted index concept, leaving Q2, Q3, Q4,
ranking, sharding and the indexing pipeline open. All now answered.

**The headline result:** Day 33 concluded this needed a distributed system with a
coordinator, query fan-out and result merging. **Changing the partitioning axis
from document to tenant deleted that entire problem.** Same data, same scale, one
decision, half the architecture gone.

---

## The Settled Design

```
FRESHNESS   dual index — main (50 GB, disk, sharded) + live (in RAM, ~60s)
            query both, merge; background compaction folds live into main
            costs: operational + complexity    buys: read-your-own-writes

ISOLATION   one index per tenant, ~8,000 of them at ~6 MB each
            costs: operational burden          buys: correctness + latency

SHARDING    partition by TENANT, not by document
            → every query touches ONE 6 MB index
            → no fan-out, no coordinator, no merge, no tail latency
            → the 50 GB total never constrains anything

RANKING     text signals (BM25) matter less than workflow state
            recency + unpaid + amount predict intent better than word counts
            corpus is ~12,500 records per tenant, not a billion
```

---

## Q2 — Which Constraint Breaks Worst? (8/10)

**Answer: Freshness > Latency > Relevance.** Correct ranking.

### Freshness #1 — reasoned via Day 36 ⭐

> *"Read after write is not possible."*

Direct transfer from Day 36, one day later. The accountant **made the write** and
knows the invoice exists. Search saying otherwise doesn't look slow or unhelpful —
it looks **broken**. Same anomaly class as the vanished refund, different surface.

### Relevance #3 — correct by instinct; here is the principled reason

```
Google ranks:      billions of documents   → relevance is everything
SalesPoint ranks:  ~12,500 of YOUR records → relevance barely matters
```

Search "ACME" and get ~50 hits the user can sort by date and eyeball.
Sophisticated relevance scoring solves a problem this corpus doesn't have.
**Web-search intuitions don't transfer to a bounded per-tenant corpus.**

### Latency #2 — right rank, wrong reason

Claimed *"hashmap very fast, not a big constraint."* True on **one** server. But
Day 33 concluded 50 GB must shard, and a fan-out query is as slow as its
**slowest** shard, not its average:

```
Query → coordinator → shard 1 (12ms)
                    → shard 2 (15ms)
                    → shard 3 (180ms)  ← GC pause / slow disk / noisy neighbour
                    ─────────────────
        merge, respond:  180ms
```

With 10 shards you hit *someone's* bad moment on most queries.
**Latency stops being free the moment you fan out.**
(Resolved later in the session — partitioning by tenant removes fan-out entirely,
so this cost disappears.)

---

## Q3 — Freshness Architecture (7.5/10)

**Decision: yes, immediately.** Correct for a back-office tool.
**Guarantee: read-your-own-writes.** Correct, correct observer.

### ⚠️ The Day 36 mechanism does NOT port

Proposed sticky sessions as the fix. It cannot work here.

```
DATABASE:   Leader has the refund ✅ ──▶ Follower doesn't yet ❌
            Fix: route the read to the leader. The data IS there.

SEARCH:     DB has the invoice ✅
                    │
                    ▼  indexing pipeline: tokenize → invert → merge
            Index doesn't have it ❌  ...on ANY machine
```

**No index anywhere has it yet.** Not a stale copy — a *not-yet-built* copy.
Routing elsewhere reaches a machine that is equally ignorant.

> Replication lag is **a copy being behind**.
> Index lag is **a derived structure not yet rebuilt**.
> Different problem, different fix.

Applies to every **derived** store: materialised views, CQRS projections (Day 15),
analytics rollups, caches. Anything requiring transformation before it is readable
cannot be fixed by routing.

### The actual fix: two structures

```
Query "INV-5521"
      │
      ├──▶ MAIN INDEX     50 GB, disk, sharded, merged periodically
      │                    everything older than a few seconds
      │
      └──▶ LIVE INDEX     small, in RAM, last ~60s of writes
                           INV-5521 is here milliseconds after the DB write
      │
      ▼
   merge results → respond
```

Essentially what Lucene/Elasticsearch do with segments and refresh intervals.

### Segments are immutable — and this is the Day 32 pattern again

```
Live index fills (60s) → flushed to disk AS-IS, becomes a new small SEGMENT
                          main index is never modified in place

Segments accumulate:  [big][small][small][small][small]
                          ↓ background compaction
                      [bigger]
```

Immutable files need no locking under concurrent reads; compaction writes a new
file and swaps a pointer. **Same shape as Day 32's Redis work** — append-only log
plus periodic background compaction. LSM trees, RDB+AOF and Lucene segments are
one idea in three costumes.

Merging is cheap because posting lists are **sorted by doc_id**:
```
MAIN:   acme → [1, 2, 7, 40000]
LIVE:   acme → [99001]
        ───────────────────────
MERGED: acme → [1, 2, 7, 40000, 99001]     linear walk, no re-tokenising
```

### Costs, honestly weighted

```
Complexity      ████████  dominant — two structures, merge logic, compaction
Operational     ██████    compaction fails silently; needs observability
Memory          ████      live index in RAM on every node
Latency         █         real but small; sawtooth p99 across the cycle
```

**Note:** he challenged the latency cost and was right to — I had listed four
costs as if equal and they are not. Latency here is 2 hash lookups instead of 1,
plus a sawtooth p99 as the live index fills and empties. **Challenging an
asserted cost is the Day 34 "unsourced number" behaviour generalising** — the
checkpoint said it hadn't; here it did.

---

## Q4 — Multi-Tenant Isolation (6/10)

**Chose: one giant index + tenant_id filter. Wrong fork, and for a reason that
doesn't bear on the fork** (recency ranking — which works identically either way;
scoring and partitioning are independent questions).

### First: the number was wrong, and it mattered

The question said "100K tenants"; Day 33's estimate said "100K users". He
questioned it (**good — that is new**) but replaced one unverified number with
another rather than resolving it.

Resolution comes from **Day 35's own figure — 8,000 merchants**:

```
8,000 tenants × ~12 users  ≈  100,000 users     ← matches Day 33
100,000 users × 1,000 recs =  100M records      ← matches Day 33
                              50 GB index
```

Day 33's numbers were right. **Tenants ≈ 8,000, not 100,000.**

### What that does to the architecture

```
100M records / 8,000 tenants = 12,500 records per tenant
12,500 × 0.5 KB              = ~6 MB per tenant index
```

```
BY DOCUMENT                          BY TENANT
Query → coordinator                  Query → route on tenant_id
      → shard 1  ┐                         → ONE index, 6 MB
      → shard 2  ├ fan-out                       ↓
      → shard 3  ┘                          respond
      → merge, wait for slowest
      → tail latency problem          No fan-out. No merge.
                                      No coordinator. No tail latency.
```

**A tenant never searches another tenant's documents, so no query spans the
50 GB.** Total index size stops being an architectural constraint — it becomes a
storage line item. ~8,000 indexes over ~10 machines, ~800 per machine, one index
per query.

### The comparison

| | One giant index + filter | **Index per tenant** ✅ |
|---|---|---|
| **Guarantee** | Isolation enforced by *code* | Isolation enforced by *physics* |
| **Query work** | Scan lists spanning 8,000 tenants, discard ~99.99% | Touch only your own 6 MB |
| **Leak risk** | One missing `WHERE tenant_id` = breach | Data isn't there to leak |
| **Cost** | Wasted query work; **correctness risk** | 8,000 objects to operate |
| **Noisy neighbour** | One huge tenant slows everyone | Contained |

For fintech the leak row decides it. A filter bug is a **regulatory event**, not a
bug report. Physical isolation makes the failure *impossible* rather than
*unlikely*, and 8,000 indexes is an operations problem — a far better problem.

**Refinement (Day 17/18 pattern):** the largest merchants will hold 500,000
records, not 12,500. Give those a dedicated index and machine — **sub-sharding the
hot tenant**, already known from consistent hashing.

### The cost sentence

> *"One index per tenant. **What it costs me is running 8,000 separate indexes —
> creating, monitoring, backing up, rebuilding — in operational burden. What it
> buys me is physical tenant isolation and single-shard queries with no
> fan-out.**"*

```
HAND OVER  →  operational burden (8,000 objects to run)
GET BACK   →  correctness (isolation is physical, not a WHERE clause)
              latency     (one 6 MB index, no fan-out, no tail)
```

Good trade for fintech: spend the cheap currency (ops work — hireable,
automatable) to buy the expensive one (correctness — unrecoverable once spent).
The giant index makes the opposite trade.

---

## Relevance: What It Actually Looks Like

Accountant searches `ACME`. Three of fifty hits:

| Doc | Content | "acme" appears |
|---|---|---|
| **INV-5521** | ACME Corp — $12,000 — **unpaid, yesterday** | 1× |
| **INV-0012** | ACME Corp — $340 — paid, **3 years ago** | 1× |
| **INV-3300** | Beta Ltd — *"ACME transferred to Beta; ACME contract ended; see ACME history"* | 3× |

Wanted: **INV-5521**. Pure text matching ranks **INV-3300** first — and it isn't
even an ACME invoice. **Word frequency has almost nothing to do with intent.**

### TF-IDF / BM25

```
TF  (term frequency)   how often the word appears in THIS doc    ↑ score
IDF (inverse doc freq) how RARE the word is across all docs      ↑ score
```

IDF is the clever half. For `"ACME invoice"`: `invoice` appears in all 1,000 docs
→ weight ≈ 0; `ACME` appears in 50 → high weight. The rare word drives ranking.

**BM25** adds: term frequency **saturates** (the 10th "acme" adds nearly nothing
over the 3rd — killing INV-3300's advantage) and normalises by document length —
the Day 33 insight, already reached independently.

> **He re-derived IDF unprompted** on `INV-5521`: *"INV is a common word polluting
> the search; 5521 is unique, rare."* True twice — a rare term means a **short
> posting list** (fast intersection) *and* a **high IDF weight** (good ranking).

### But for SalesPoint, text signals are the wrong signals

BM25 still ranks a three-year-old paid $340 invoice equal to yesterday's unpaid
$12,000 one, because text cannot see business meaning.

```
score = text_match × w1
      + recency    × w2      ← last 90 days matter enormously
      + unpaid     × w3      ← you search for what you must act on
      + amount     × w4      ← big invoices are memorable
```

> Web search ranks on **text**, because that is all it has.
> Business search ranks on **workflow state**, because it has something better.

The deeper reason relevance sits at #3: the version needed here is a weighted sort
on fields already present, not an information-retrieval system.

---

## Terminology Corrections

Two conflations, both worth fixing before an interview.

**1. "INV is an index, 5521 is another index."** They are **terms** inside *one*
index.
```
ONE INDEX (the whole dictionary):
   inv    → [Doc12, Doc88, Doc5521, ...]     ← term, and its posting list
   5521   → [Doc5521]                        ← another term
```
The **index** is the map. **Terms** are its keys. **Posting lists** are its values.
"Query both indexes" = look up term `inv` in main *and* in live — two structures,
same term.

**2. "10B × 40 terms = 400B unique terms."** Those are **postings**, not unique
terms. **Vocabulary** (distinct words anywhere) is ~2–5M and stops growing.
**Postings** are entries in posting lists and grow forever.

---

## Arithmetic: The Failure Mode Moved

**Error this session:** `100K × 10` computed as 10M. Correct is 1M.
Same class as Day 33's `100K × 1K` read as 1M. Big-number multiplication
**nested inside other reasoning** is where it slips — Day 35 looked clean because
the multiplications stood alone.

### The technique — count zeros, don't estimate

```
100K × 10  =  10⁵ × 10¹  =  10⁶  =  1,000,000      (said 10M)
100K × 1K  =  10⁵ × 10³  =  10⁸  =  100,000,000    (said 1M, Day 33)
```
**Digits multiply, zeros add.** 1 × 1 = 1, and 5 + 1 = 6.
```
10³ = thousand (K)   10⁶ = million (M)   10⁹ = billion (B)   10¹² = trillion (T)
```

### Reps — and the failure mode moved to units

```
1)  8,000 × 12,500   = 100,000,000        ✅ correct, zero-counting worked
2)  12,500 × 0.5 KB  = 6,250 KB = 6.25 MB  ⚠️ said 6.1 KB — right digits, wrong unit
3)  8,000 × 6 MB     = 48,000 MB = 48 GB   ⚠️ said 40 MB
```
Zeros are no longer being lost; **unit steps are not being taken**. Every ×1,000
moves one rung: `KB → MB → GB → TB`.

### Self-consistency check ⭐

Rep 3 lands at **48 GB**. Day 33 estimated **50 GB** by a completely different
route. Two independent paths to the same number — the model is sound. Worth doing
deliberately: arriving at a figure twice from different directions catches errors
that do not announce themselves.

---

## Session Note — Load and Pacing

He said, unprompted and without blame: *"It's a lot for me… give me time to
digest. Search one is entirely different. I spent much time, still I can't come to
any final conclusion."*

**Two things are true.**

**Search genuinely is different**, and he identified this himself on Day 33.
Days 20–32 sat on caching, queuing, storage, replication — patterns backed by 12
years of intuition, where the work was *arranging familiar pieces*. Search is
information retrieval: inverted indexes, TF-IDF, posting lists, segments. No prior
anchor. The confidence dip is appropriate, not regression.

**But he did reach a conclusion** — it arrived in pieces and he never saw them
side by side. The design at the top of this file is complete, and Day 33 had none
of it. Showing the assembled result was what made it feel finished.

**Pacing note for Days 38–40:** deliver one concept, then let it settle, rather
than chaining corrections. Today ran ~60 mins across four threads (Q2/Q3/Q4 plus
arithmetic remediation) and saturation was visible by the end.

---

## Key Takeaways

1. **Changing the partitioning axis can delete an architecture.** Shard by tenant,
   not document: no fan-out, no coordinator, no merge, no tail latency. The 50 GB
   total never constrains anything.
2. **Derived stores can't be fixed by routing.** Replication lag = a copy behind.
   Index lag = a structure not yet rebuilt. Sticky sessions fix the first, never
   the second. Applies to projections, materialised views, rollups, caches.
3. **Physical isolation beats a WHERE clause** when the currency at risk is
   correctness — 8,000 indexes is an ops problem, a cross-tenant leak is a
   regulatory event.
4. **Immutable segments + background compaction** is one pattern with many names:
   Lucene segments, LSM trees, Redis RDB+AOF (Day 32).
5. **Business search ranks on workflow state, not text.** Recency and payment
   status predict intent far better than word counts, because the corpus is
   bounded and small.
6. **Terms ≠ indexes. Postings ≠ vocabulary.**
7. **Count zeros as exponents; then step the units.** And check a number twice by
   two different routes.

---

## Next: Day 38 — Consistency Re-Test

Day 36 material, cold, two days later. Round 3 re-run plus two new scenarios.
**Gate for Phase 3: ≥ 8/10.**

Watch for the relapse flagged on Day 36 — sorting data into "critical" and
"non-critical" instead of asking who the observer is and what anomaly they would
notice.
