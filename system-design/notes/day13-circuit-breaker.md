# Day 13 — Circuit Breaker Pattern

**Date:** 2026-07-31  
**Time:** 15 minutes  

---

## The Problem — Cascading Failures

In microservices, services call each other. If one service goes slow or down, without protection the callers pile up waiting threads — and they go down too. This is a **cascading failure**.

```
  [Orders] → [Payments] ← SLOW / DOWN

  1. Orders waits 30s for Payments...
  2. More Orders requests arrive, all waiting...
  3. Orders thread pool exhausts
  4. [API Gateway] → [Orders] ← NOW SLOW TOO
  5. Gateway threads exhaust
  6. Entire system down ❌
```

> One slow dependency can bring down the whole system — even if everything else is healthy.

**Retry alone makes it worse** — if Payments is down, retrying hammers it with even more traffic while it's trying to recover.

---

## The Circuit Breaker — The Electrical Analogy ⚡

Just like an electrical circuit breaker — when current (failures) exceeds a threshold, the breaker **trips open** and stops the flow. It protects everything upstream.

```
Normal:     [Orders] ──CLOSED──▶ [Payments]   ✅ requests flow through
Tripped:    [Orders] ──OPEN──✖  [Payments]    ❌ fail immediately, no waiting
Recovering: [Orders] ──HALF──▶  [Payments]    🔍 test one request through
```

---

## The Three States

### 1. CLOSED — Normal Operation ✅

All requests pass through. The breaker counts failures silently.

```
[Orders] ──────────────────────▶ [Payments]
          request 1 ✅
          request 2 ✅
          request 3 ❌ (failure count: 1)
          request 4 ❌ (failure count: 2)
          request 5 ❌ (failure count: 3 → THRESHOLD HIT → trips OPEN)
```

**Threshold example:** 5 failures in 10 seconds → trip open

---

### 2. OPEN — Fail Fast ❌

The breaker stops ALL requests immediately — no network call made. Returns a cached response or error instantly.

```
[Orders] ──OPEN──✖  [Payments]  (not even called)
          → instant BrokenCircuitException
          → caller gets fallback response in <1ms
          → Payments gets ZERO traffic (can recover)
```

**Why this is good:**
- Orders threads are freed immediately — no 30s wait
- Payments gets breathing room to recover
- Upstream services stay healthy

After a **timeout** (e.g. 30 seconds), the breaker moves to Half-Open to test recovery.

---

### 3. HALF-OPEN — Testing Recovery 🔍

One probe request is let through. Based on the result, the breaker either:
- ✅ Succeeds → **CLOSES** (back to normal)
- ❌ Fails → **OPENS** again (wait another 30s, try again)

```
After 30s timeout:
  [Orders] ──HALF-OPEN──▶ [Payments]
                            ↓
              ✅ 200 OK → CLOSED (normal operation resumes)
              ❌ Error  → OPEN   (wait another 30s)
```

---

## State Machine — Full Picture

```
                  ┌─────────────────────────────┐
                  │                             │
                  ▼                             │
  ┌────────────────────┐    threshold       ┌───┴──────────────────┐
  │      CLOSED        │   exceeded ──────▶ │        OPEN          │
  │  (normal, counting)│                    │  (fail fast, no call) │
  └────────────────────┘                    └───┬──────────────────┘
              ▲                                 │
              │ probe                           │ timeout
              │ succeeds                        │ expires
              │                                 ▼
              │                    ┌────────────────────┐
              └────────────────────│     HALF-OPEN       │
                                   │  (one probe request)│
                                   └────────────────────┘
                                         │
                                         │ probe fails
                                         ▼
                                       OPEN (reset timer)
```

---

## Circuit Breaker vs Retry — Key Difference

These two patterns serve **opposite purposes** and must be used together correctly.

| | Retry | Circuit Breaker |
|--|--|--|
| **Purpose** | Handle transient blips | Stop calling a broken service |
| **When to use** | Short network hiccup (ms) | Service is down or degraded (seconds/minutes) |
| **Effect on downstream** | Increases traffic | Reduces traffic to zero |
| **Failure type** | Occasional single failures | Sustained failure pattern |

**Combined correctly:**

```
Request flow:
  1. Circuit Breaker checks: is circuit OPEN? → fail fast immediately
  2. If CLOSED: pass to Retry
  3. Retry attempt 1 fails → Retry attempt 2 → Retry attempt 3 → all fail
  4. All retries exhausted → exception bubbles up to Circuit Breaker
  5. CB counts this as 1 FAILURE (not 3 — retries are invisible to CB)
  6. If failure threshold hit → OPEN the circuit

  MaxRetryAttempts = 3 means: 1 original + 3 retries = 4 total HTTP calls per request
```

> **Rule:** Retry for transient errors. Circuit Breaker for sustained failures. Never retry when the circuit is open — CB wraps Retry, so when CB is OPEN, Retry never runs.

---

## Fallback Strategies

When the circuit is OPEN, you need a fallback — what do you return to the caller?

| Strategy | Example | When to Use |
|----------|---------|-------------|
| **Cached response** | Return last known payment methods (saved cards) | Data that rarely changes — stale is acceptable |
| **Default value** | Return `{ "discount": 0 }` | Feature degrades gracefully, user unaffected |
| **Error response (503)** | Return 503 with `Retry-After: 30` header | Payment charge — cannot fake it, tell user honestly |
| **Queue for later** | Write to queue, process when service recovers | Non-urgent writes — loyalty points, receipts |

> **Decision rule:** Ask "what does the user lose if I use a fallback?"  
> Charging a card → can't fake → **503**.  
> Listing saved cards → stale list is fine → **cache**.  
> Updating loyalty points → 30s delay unnoticeable → **queue**.

> **Always include `Retry-After` header on 503** — never return a bare error. Tell the client exactly when to retry.

```csharp
// Fallback example: return cached data when Payments is down
var result = await circuitBreaker.ExecuteAsync(
    () => paymentsClient.GetMethodsAsync(userId),
    fallback: () => cache.GetLastKnown(userId)  // graceful degradation
);
```

---

## Bulkhead Pattern — Related Concept

Named after ship bulkheads that isolate compartments — a leak in one section doesn't sink the ship.

### Requests vs Threads — The Key Distinction

**Threads don't stack up from speed — they stack up from SLOWNESS.**

```
Payments responds fast (50ms):
  Thread 1: →[send]→[wait 50ms]→[receive]→ FREE ✅
  Thread 2: →[send]→[wait 50ms]→[receive]→ FREE ✅
  10 requests/sec → only ~1 thread busy at a time ✅

Payments responds slow (5 seconds):
  Thread 1: →[send]→[waiting........5s........]→ BLOCKED 🔴
  Thread 2: →[send]→[waiting........5s........]→ BLOCKED 🔴
  Thread 3: →[send]→[waiting........5s........]→ BLOCKED 🔴
  ...
  Thread 10: →[send]→[waiting.......5s........]→ BLOCKED 🔴
  11th request → NO FREE THREAD → REJECTED → 503
```

### Without Bulkhead — Shared Pool Problem

```
  ┌──────────────────────────────────┐
  │  Shared Thread Pool (50 threads) │
  │  [Payments calls filling up...]  │ ← Payments slow → ALL 50 threads blocked
  │  [Orders calls blocked too]      │ ← Orders can't run even though healthy!
  └──────────────────────────────────┘
```

### With Bulkhead — Isolated Pools Per Dependency

```
  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
  │  Payments Pool      │  │  Inventory Pool      │  │  Orders Pool        │
  │  Max: 10 threads    │  │  Max: 10 threads     │  │  Max: 20 threads    │
  │                     │  │                      │  │                     │
  │  [call][call][call] │  │  [call][call]        │  │  [call][call][call] │
  │  [call][call][call] │  │                      │  │  [call][call]       │
  │  [call][call][call] │  │                      │  │                     │
  │  [call]             │  │                      │  │                     │
  │  11th → REJECTED    │  │  Unaffected ✅       │  │  Unaffected ✅      │
  │  503 instantly      │  │                      │  │                     │
  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

Payments pool hits max → **only Payments calls are rejected instantly (503)**. Inventory and Orders pools are completely separate — unaffected.

### CB + Bulkhead — Full Request Flow

```
Incoming request to Orders:
    │
    ▼
[Bulkhead Check]  → Payments pool full? → YES → 503 instantly (no wait, no retry)
    │ Pool has space
    ▼
[Circuit Breaker] → Circuit OPEN?       → YES → 503 instantly (BrokenCircuitException)
    │ Circuit CLOSED
    ▼
[Retry]           → Make the call, retry up to N times on failure
    │ All retries exhausted → exception
    ▼
[CB failure count +1] → threshold hit? → OPEN circuit
```

| Pattern | Protects Against | Response When Triggered |
|---------|-----------------|------------------------|
| **Bulkhead** | Slow dependency eating ALL threads | 503 — pool full |
| **Circuit Breaker** | Dead dependency causing long waits | 503 — fail fast |
| **Retry** | Brief transient network blips | Transparent to caller |

> **Mental model:** Bulkhead = *how many threads allocated per dependency*. Circuit Breaker = *should we even try calling*. They work at different levels and complement each other.

**Circuit Breaker + Bulkhead = full isolation:** CB stops calls to dead services; Bulkhead caps blast radius per dependency so a slow service can never starve the whole thread pool.

---

## C# Angle — Polly Library

**Polly** is the standard resilience library in .NET. Used everywhere in ASP.NET Core.

### Basic Circuit Breaker

```csharp
var circuitBreaker = Policy
    .Handle<HttpRequestException>()
    .OrResult<HttpResponseMessage>(r => !r.IsSuccessStatusCode)
    .CircuitBreakerAsync(
        handledEventsAllowedBeforeBreaking: 5,   // 5 failures → OPEN
        durationOfBreak: TimeSpan.FromSeconds(30) // stay OPEN for 30s
    );
```

### With Fallback + Retry (Full Pipeline)

```csharp
// Order matters: outermost first
var policy = Policy.WrapAsync(
    // 1. Fallback — outermost, catches everything
    Policy<PaymentResult>
        .Handle<BrokenCircuitException>()
        .FallbackAsync(PaymentResult.Unavailable),

    // 2. Circuit Breaker
    Policy<PaymentResult>
        .Handle<HttpRequestException>()
        .CircuitBreakerAsync(5, TimeSpan.FromSeconds(30)),

    // 3. Retry — innermost, runs first
    Policy<PaymentResult>
        .Handle<HttpRequestException>()
        .WaitAndRetryAsync(2, _ => TimeSpan.FromMilliseconds(200))
);

var result = await policy.ExecuteAsync(() => paymentsClient.ChargeAsync(order));
```

### Polly v8 — Resilience Pipelines (Modern API)

```csharp
// .NET 8+ / Polly v8
var pipeline = new ResiliencePipelineBuilder<PaymentResult>()
    .AddRetry(new RetryStrategyOptions<PaymentResult>
    {
        MaxRetryAttempts = 2,
        Delay = TimeSpan.FromMilliseconds(200)
    })
    .AddCircuitBreaker(new CircuitBreakerStrategyOptions<PaymentResult>
    {
        FailureRatio = 0.5,          // 50% failure rate → OPEN
        SamplingDuration = TimeSpan.FromSeconds(10),
        MinimumThroughput = 5,       // need at least 5 requests to evaluate
        BreakDuration = TimeSpan.FromSeconds(30)
    })
    .Build();
```

### Register with HttpClientFactory (Recommended)

```csharp
builder.Services.AddHttpClient<IPaymentsClient, PaymentsClient>()
    .AddResilienceHandler("payments-pipeline", builder =>
    {
        builder
            .AddRetry(new HttpRetryStrategyOptions { MaxRetryAttempts = 2 })
            .AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
            {
                BreakDuration = TimeSpan.FromSeconds(30)
            })
            .AddTimeout(TimeSpan.FromSeconds(5));
    });
```

---

## When to Configure What

| Setting | Typical Value | Notes |
|---------|--------------|-------|
| Failure threshold | 5 failures / 50% rate | Tune per service SLA |
| Break duration | 30–60 seconds | Long enough for service to recover |
| Sampling window | 10–30 seconds | Wider = less noise |
| Minimum throughput | 5–10 requests | Avoid tripping on cold start |
| Retry attempts | 2–3 max | Never infinite |
| Retry delay | 200ms–1s (exponential) | Back off under load |

---

## Real World — Where You See This

| System | Usage |
|--------|-------|
| Netflix Hystrix | Pioneer — now deprecated, Resilience4j replaced it |
| Istio / Envoy | CB configured in service mesh — no app code needed |
| Azure Service Bus | Built-in dead-letter + retry policies |
| AWS SDK | Automatic retry + CB built into SDK |
| .NET HttpClientFactory | Polly integration built-in since .NET 6 |

---

## 🎯 Key Takeaway

> **Circuit Breaker = fail fast to protect the whole system. Three states: CLOSED (normal) → OPEN (fail fast, give downstream breathing room) → HALF-OPEN (probe recovery). Combine with Retry (for transient blips) and Fallback (for graceful degradation). In .NET, use Polly — register it on HttpClientFactory, not inline. Never retry when the circuit is open.**

---

## Questions to Think About

1. Orders calls Payments. Payments starts returning 500 errors. Walk through exactly what the Circuit Breaker does — from first failure to recovery. What state transitions happen and when?
2. You set `MaxRetryAttempts = 3` and `CircuitBreakerAsync(5, ...)`. A Payments outage causes 100 concurrent Orders requests. How many actual HTTP requests hit the Payments service before the circuit opens?
3. Your Circuit Breaker is OPEN. What should you return to the user — an error, a cached value, or queue the request? What factors decide which fallback strategy to choose?
