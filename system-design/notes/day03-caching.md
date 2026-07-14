# Day 3 — Caching

**Date:** 2026-07-15  
**Time:** 15 minutes  

---

## What is Caching?

Store frequently accessed data in fast memory to avoid hitting the database every time.

```
Without cache:  Request → DB (10–100ms) → Response
With cache:     Request → Redis (< 1ms)  → Response   ← 100x faster
```

---

## Where to Cache — Placement

| Layer | Where | Example |
|---|---|---|
| **Client-side** | Browser/app memory | Cached user profile in React state |
| **CDN** | Edge servers globally | Images, JS, CSS — closest to user |
| **Server-side** | Redis / in-memory | DB query results, API responses |
| **DB query cache** | Inside the database | Repeated identical SQL queries |

---

## The Cache-Aside Pattern *(most common)*

App code manages the cache manually:

```
1. Request comes in
2. Check Redis → HIT? Return cached data ✅
3. MISS? → Query DB → Store result in Redis → Return data
```

```csharp
var data = await _redis.GetAsync("user:123");
if (data == null) {
    data = await _db.GetUserAsync(123);
    await _redis.SetAsync("user:123", data, TimeSpan.FromMinutes(5));
}
return data;
```

---

## Write Strategies

| Strategy | How | Trade-off |
|---|---|---|
| **Write-through** | Write to cache AND DB together | Slower writes, always consistent |
| **Write-back** | Write to cache, DB later async | Fast writes, risk of data loss |
| **Write-around** | Write to DB only, bypass cache | Cache stays clean, first read is slow |

---

## Eviction Policies

When cache is full, what gets removed?

- **LRU** (Least Recently Used) — evicts oldest untouched item ← default Redis
- **LFU** (Least Frequently Used) — evicts least accessed item
- **TTL** (Time To Live) — expires after fixed duration

---

## ⚠️ The 3 Problems to Know

1. **Stale Data** — cache has old value after DB update  
   → Fix: invalidate cache on write + shorter TTL  
   ```csharp
   await _db.UpdateProductPriceAsync(productId, newPrice);
   await _redis.RemoveAsync($"product:{productId}"); // force fresh load
   ```

2. **Cache Stampede (Thunder Herd)** — cache expires, thousands of requests hit DB simultaneously  
   → Fix: mutex lock (only one request rebuilds cache) or TTL jitter (randomise expiry times)

3. **Hot Key** — one key gets millions of hits (e.g. celebrity profile)  
   → Fix: local in-memory cache as a second layer + shard the key across multiple Redis keys

---

## C# / Azure Context

- `IMemoryCache` — in-process cache, **single server only** ❌ breaks with horizontal scaling
- `IDistributedCache` + **Azure Cache for Redis** — shared across all servers ✅
- Always use Redis when horizontally scaled (ties back to Day 1 stateless design!)

---

## 🎯 Key Rule

> **Cache is a performance optimisation, not a data store.**  
> Always assume the cache can be cleared at any time — your system must still work correctly without it.

---

## Questions to think about

1. Does your current C# API use `IMemoryCache`? Would it break if you added a second server?
2. When your app updates a record, does it also invalidate the cache? Or does it wait for TTL to expire?
3. What's the most "hot" data in your current system — what would benefit most from caching?
