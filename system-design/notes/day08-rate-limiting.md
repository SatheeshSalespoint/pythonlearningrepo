# Day 8 — Rate Limiting

**Date:** 2026-07-22  
**Time:** 15 minutes  

---

## The Problem Rate Limiting Solves

Without rate limiting, a single bad actor can exhaust your service:

```
Client (malicious / buggy) → 10,000 req/sec → [Your API] → 💥 down
```

Rate limiting controls **how many requests** a client can make in a given time window — protecting availability for everyone.

---

## The 4 Algorithms

| Algorithm | How It Works | Allows Burst? | Best For |
|-----------|-------------|---------------|---------|
| **Fixed Window** | Count resets every N seconds | ✅ At boundaries | Simple use cases |
| **Sliding Window** | Rolling count over last N seconds | ❌ No | Accurate enforcement |
| **Token Bucket** | Tokens refill at fixed rate; 1 token = 1 request | ✅ Short bursts | APIs with bursty traffic |
| **Leaky Bucket** | Requests drain at a fixed output rate | ❌ No | Strict rate (payment APIs) |

### Fixed Window Boundary Problem

```
Window:  00:00 ──────── 01:00 | 01:00 ──────── 02:00
Requests:      95 at 00:59   +   95 at 01:01 = 190 in 2 seconds ← burst!
```

Sliding window fixes this — it considers the last 60 seconds from *now*, not a fixed clock slot.

---

## Redis Implementation — Atomic Counters

**Fixed window** — naive approach has a race condition:

```
INCR key        ← two threads read 0, both write 1 — undercounting
EXPIRE key 60
```

**Fix:** Use a Lua script (atomic in Redis):

```lua
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
```

**Sliding window** with sorted set (ZSET):

```
ZADD user:123 <timestamp_ms> <uuid>
ZREMRANGEBYSCORE user:123 0 <now - window_ms>
ZCARD user:123   ← accurate current count
```

> More accurate but uses more memory — choose based on how strictly you need to enforce the limit.

---

## Rate Limit Key Design

```csharp
// Bad — too broad
key = "rl:global"

// Good — layered, specific
key = $"rl:{tenantId}:{userId}:{endpoint}"
key = $"rl:{apiKey}:global"
key = $"rl:{tenantId}:plan:{tier}"   // tenant billing tier
```

**Multi-tenant SaaS:**
- Free plan → 100 req/day
- Pro plan → 10,000 req/day
- Enterprise → unlimited

Store the limit value in the tenant/user record — **never hardcoded**.

---

## Multi-Dimensional Limits

Layer limits to protect at different granularities:

```
Per second  →  10 req/sec    (burst protection)
Per minute  →  100 req/min   (normal throttling)
Per day     →  10,000 req/day (quota enforcement)
Per endpoint → POST /ai/generate = 5/min (expensive ops)
```

---

## C# — ASP.NET Core Built-In (.NET 7+)

```csharp
builder.Services.AddRateLimiter(o => o
    .AddFixedWindowLimiter("api", opts => {
        opts.PermitLimit = 100;
        opts.Window = TimeSpan.FromMinutes(1);
        opts.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        opts.QueueLimit = 10;
    }));

app.UseRateLimiter();

// On endpoint
[EnableRateLimiting("api")]
public async Task<IActionResult> GetTasks() { ... }
```

---

## Response Headers — Clients Need Feedback

Always return these so well-behaved clients back off automatically:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1721613600   ← Unix timestamp when window resets
Retry-After: 47                 ← seconds until they can retry
```

---

## Where to Enforce

```
Client → [API Gateway] → [Load Balancer] → [Service]
              ↑
       Best place — centralised, before traffic hits your code
```

| Layer | Tool | Notes |
|-------|------|-------|
| **API Gateway** | Kong, AWS API GW, Azure APIM | Easiest — zero app code |
| **Load Balancer** | NGINX, HAProxy | Good for IP-based limits |
| **Application** | ASP.NET Core middleware | Fine-grained per-endpoint control |
| **In-process only** | ❌ Avoid | Breaks when horizontally scaled |

> **Always store counters in Redis** — in-memory counters don't work across multiple instances.

---

## Redis Failure — What Happens to Your Rate Limiter?

| Strategy | Behaviour | Risk |
|----------|-----------|------|
| **Fail open** | Allow all traffic | DDoS exposure |
| **Fail closed** | Reject all traffic | Full outage |
| **Local fallback** | Each instance applies a conservative local limit | Balanced |

```csharp
try {
    allowed = await redisRateLimiter.CheckAsync(key);
} catch (RedisException) {
    // Fail open with reduced local limit (10% of normal)
    allowed = localFallbackLimiter.Check(key);
}
```

> Document this decision — payment APIs fail closed; CDN APIs fail open.

---

## Rate Limiting vs Throttling vs Circuit Breaker

| Pattern | Protects | Trigger | Client Sees | Direction |
|---------|----------|---------|-------------|-----------|
| **Rate Limiting** | Your service from bad clients | Count exceeded | `429` — hard reject | Inbound |
| **Throttling** | Client experience under load | System pressure | Delayed response — still served | Inbound |
| **Circuit Breaker** | Your service from broken dependencies | Errors > threshold | `503` — fail fast | Outbound |

```
Rate Limiter:    101st request → GONE immediately
Throttling:      101st request → "wait 2 seconds... now processing"
Circuit Breaker: downstream broken → stop calling it, return fallback instantly
```

> **Rate limit** = fixed gate — pass or don't  
> **Throttle** = flexible valve — controls flow speed  
> **Circuit Breaker** = kill switch — protects you from someone else's failure

---

## Adaptive Rate Limiting (Advanced)

Don't use static limits — adjust dynamically based on system health:

```
CPU > 80%         → cut limit by 50%
Queue depth > 10k → reduce new requests
Error rate > 5%   → shed load automatically
```

Used by Cloudflare, Stripe, Netflix. In .NET: combine with `System.Threading.Channels` for backpressure.

---

## Testing Rate Limiters — Often Skipped

```csharp
[Fact]
public async Task Returns429_OnLimitExceeded() {
    for (int i = 0; i <= 100; i++)
        responses.Add(await client.GetAsync("/api/tasks"));

    Assert.Equal(HttpStatusCode.TooManyRequests, responses.Last().StatusCode);
    Assert.True(responses.Last().Headers.Contains("Retry-After"));
}
```

Also test:
- **Window boundary burst** — send 95 requests at end of window + 95 at start of next
- **Redis failure fallback** — what happens when Redis is down?
- **Concurrent requests** — race conditions in counter increments

---

## 🎯 Key Takeaway

> **Rate limiting is a contract with your clients** — the algorithm, headers, and failure behaviour must all be intentional and documented. Always use Redis for distributed counters (never in-memory when scaled), design keys per tenant/user/endpoint, layer limits at multiple time granularities, and define a Redis failure strategy. Most rate limiter outages happen during Redis failures or incorrect key design in multi-tenant systems.

---

## Questions to Think About

1. Your API has Free (100/day) and Pro (10,000/day) plans. A Pro user shares their API key with 50 people — what rate limit key design would catch this?
2. Redis goes down during peak traffic. Your rate limiter fails open — what's your fallback strategy to still protect the service?
3. You have an expensive `POST /ai/generate` endpoint. Would you use token bucket or fixed window, and why?
