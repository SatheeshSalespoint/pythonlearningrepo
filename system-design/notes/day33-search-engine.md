# Day 33: Search Engine (Basic) — Inverted Index Foundations

**Date:** 2026-09-03  
**Duration:** ~30 mins  
**Status:** 🔄 In Progress (Concept foundation done, architecture pending)  
**Difficulty:** Medium → Hard (new mental model)  
**Confidence Level:** 5/10 (new territory — inverted index understood, scale/architecture pending)  
**Communication Level:** N/A (design-only day)

---

## Session Note

Stopped early. The inverted index concept landed, but scale estimation and
architecture need a fresh session. **Resume from "Open Questions" below.**

---

## Key Distinction Learned: Autocomplete ≠ Search Engine

This was the main unlock today. Day 24 (Autocomplete) and Day 33 (Search Engine)
are the two halves of a search box, and they are **completely different systems**.

| | Autocomplete (Day 24 ✅) | Search Engine (Day 33) |
|---|---|---|
| **Fires** | Every keystroke | Once, on Enter |
| **Input** | Prefix: `"pyth"` | Full query: `"python web framework"` |
| **Output** | Query *suggestions* | Ranked *documents* |
| **Data structure** | **Trie** (prefix tree) | **Inverted index** (word → doc list) |
| **What's indexed** | ~1M popular queries | 1B+ document *contents* |
| **Latency budget** | <5ms (typing must feel instant) | <200ms (user accepts a beat) |
| **Ranking by** | Popularity / frequency | **Relevance** + popularity |

**Trie answers:** *"What words start with `pyth`?"*  
**Inverted index answers:** *"Which of my 100M documents contain `python` AND `framework`, and which is most relevant?"*

---

## Core Concept: The Inverted Index

### Why "inverted"?

A **forward** index maps document → its contents (the natural direction).
An **inverted** index flips it: word → the documents containing it.

### Worked Example (SalesPoint invoices)

**Documents:**
```
Doc1 (INV-001): "Payment received from ACME Corp for consulting services"
Doc2 (INV-002): "Payment pending from ACME Corp for software license"
Doc3 (INV-003): "Refund issued to Beta Ltd for consulting"
```

**Step 1 — Tokenize** (split to words, lowercase, drop stop words `from`/`for`/`to`):
```
Doc1 → payment, received, acme, corp, consulting, services
Doc2 → payment, pending, acme, corp, software, license
Doc3 → refund, issued, beta, ltd, consulting
```

**Step 2 — Invert** (one entry per *unique word* in the whole corpus):
```
payment     → [Doc1, Doc2]
received    → [Doc1]
acme        → [Doc1, Doc2]
corp        → [Doc1, Doc2]
consulting  → [Doc1, Doc3]
services    → [Doc1]
pending     → [Doc2]
software    → [Doc2]
license     → [Doc2]
refund      → [Doc3]
issued      → [Doc3]
beta        → [Doc3]
ltd         → [Doc3]
```

**Step 3 — Query** `"acme consulting"`:
```
acme       → [Doc1, Doc2]
consulting → [Doc1, Doc3]
──────────────────────────
Intersect  → [Doc1]         ← only doc containing BOTH

Result: INV-001
```

**Why it's fast:** no document is ever scanned. Two hash lookups + a set intersection.

### ⚠️ Misconception Corrected

Initial (wrong) mental model: index keyed by *character count*
```
10K chars → [Doc1]
20K chars → [Doc2, Doc1]
```

Correct: **the key is each individual WORD**, never the document size or char count.

### Where document size *does* matter — Ranking, not indexing

```
Query: "consulting"

Doc A:     10 words, "consulting" ×3  → 30%   of doc is about it
Doc B: 10,000 words, "consulting" ×3  → 0.03% of doc is about it

Doc A ranks higher
```

This is the **normalization** step inside TF-IDF / BM25 — term frequency divided
by document length. So the size instinct was right, just belongs in *ranking*.

### What production indexes actually store

```
"consulting" → [
    {doc: 1, count: 3, positions: [5, 40, 88]},
    {doc: 3, count: 1, positions: [6]}
]
```
- `count` → feeds the relevance score
- `positions` → enables **phrase search** (`"consulting services"` needs adjacency)

---

## Scale Estimation (corrected)

### Records

```
100,000 users × 1,000 records each = 100,000,000 = 100M records
```
> **Error caught:** originally computed as 1M. 100K × 1K = 100M, not 1M — off by 100×.
> Recurring weakness first flagged Day 22 — *write out the zeros on big numbers*.

### Index size — derive from TEXT, don't guess a multiplier

```
Step 1 — searchable text per invoice:
  Invoice number    "INV-5521"                      ~10 bytes
  Customer name     "ACME Corporation Ltd"          ~20 bytes
  Line descriptions "Consulting services Q3 2026"  ~100 bytes
  Notes / memo      free text                      ~200 bytes
  ──────────────────────────────────────────────────────────
  ≈ 330 bytes ≈ ~50 words

Step 2 — unique terms after stop-word removal & dedup:  ~40 terms

Step 3 — cost per posting entry:
  doc_id     4 bytes
  frequency  1 byte
  positions  ~4 bytes
  ─────────────────
  ~9 bytes

Step 4 — multiply:
  40 terms × 9 bytes ≈ 360 bytes  →  round to ~0.5 KB per record
```

**Working formula for text-light fintech records:**
```
Index size ≈ records × 0.5 KB

  1M records →  500 MB
 10M records →    5 GB
100M records →   50 GB    ← SalesPoint
```

### Query volume

```
100,000 users × 100 searches/day = 10,000,000 searches/day

10,000,000 ÷ 86,400 sec ≈ 116 searches/sec   (average)
```
> **Error caught:** originally computed 1 req/sec — the 100K users were left out
> of the multiplication entirely. Off by ~10,000×.

### Peak multiplier

```
Conservative (100×, as used Day 30):  116 × 100 = 11,600 req/sec
Realistic derivation:
    80% of traffic in 8 business hours   → 3× concentration
    End-of-day settlement burst          → 4× on top
    ──────────────────────────────────────────────────
    ≈ 12×                                 116 × 12 ≈ 1,400 req/sec
```
Note: activity types (invoices, receipts, reports) are **concurrent**, they do
not stack as multipliers.

### Scale summary

| Metric | Value |
|---|---|
| Records | **100M** |
| Index size | **~50 GB** |
| Avg QPS | **~116/sec** |
| Peak QPS (realistic 12×) | **~1,400/sec** |
| Peak QPS (conservative 100×) | **~11,600/sec** |

### 🔑 Why the arithmetic mattered

```
Wrong estimate:    1M records →  500MB index
                   → fits in RAM on ONE server → simple, done

Correct:         100M records →   50GB index
                   → does NOT fit comfortably on one box
                   → must SHARD across ~5-10 machines
                   → queries fan out, then MERGE results
                   → now needs a coordinator node
```

**A 100× arithmetic error flipped the architecture from "single server" to
"distributed system with a coordinator."** This is why interviewers push on the math.

---

## Open Questions — RESUME HERE NEXT SESSION

### Q2: Which constraint breaks worst?

Pick the one that generates the angriest support ticket:

- **A) Latency** — search takes 3s instead of 200ms
  > *"So slow I gave up and used the filter instead"*
- **B) Relevance** — the right invoice is on page 4, not #1
  > *"Searched ACME, got 200 results, couldn't find mine"*
- **C) Freshness** — new invoice not searchable for 10 minutes
  > *"I just created it and search says it doesn't exist"*

*Why it matters:* these three pull against each other — you cannot maximize all three.
Latency wants precomputation; relevance wants expensive scoring; freshness wants
constant index writes.

### Q3: Index freshness requirement

```
10:00:00 — accountant creates invoice INV-5521
10:00:05 — accountant searches "INV-5521"
Must it be found?
```

| Answer | Architecture | Complexity |
|---|---|---|
| Yes, immediately | Dual index: large static + small live, query both, merge | ⭐⭐⭐ |
| ~1 minute is fine | Micro-batch: buffer writes, merge every 60s | ⭐⭐ |
| Next day is fine | Nightly full rebuild, serve read-only | ⭐ |

### Q4: Multi-tenant isolation

Tenant A must **never** see Tenant B's invoices.

- **One giant index** + `tenant_id` filter at query time?
- **One index per tenant** (100K tenants = 100K small indexes)?

Big architectural fork — real consequences either way.

---

## Still To Cover (Day 34 continuation)

- [ ] Answer Q2, Q3, Q4
- [ ] Ranking: TF-IDF vs BM25 — how relevance is actually scored
- [ ] Sharding strategy: by document vs by term
- [ ] Query fan-out and result merging across shards
- [ ] Indexing pipeline: how documents get into the index
- [ ] Caching layer for repeated queries

---

## Honest Assessment

**What landed today:**
- ✅ Autocomplete vs search engine are different systems (real unlock)
- ✅ Inverted index structure — demonstrated correctly on an unseen exercise
- ✅ Where document length belongs (ranking, not indexing)

**What didn't:**
- ⚠️ Scale arithmetic — two large errors (100× on records, 10,000× on QPS)
- ⚠️ Architecture not started

**Confidence: 5/10** — genuinely new territory, and lower than recent days (8-9/10).
That is expected: Days 20-32 all built on caching/queuing/storage patterns already
familiar from 12 years of backend work. Search introduces information-retrieval
concepts with no prior anchor. A dip here is normal, not regression.

**Recommendation:** carry this into Day 34 rather than starting a new system.
