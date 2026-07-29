# Day 12 — Service Discovery

**Date:** 2026-07-30  
**Time:** 15 minutes  

---

## The Problem — Why Service Discovery Exists

In a monolith, everything is in-process — no network addresses to track. In microservices, services need to call each other over the network.

**The naive approach: hardcode addresses**

```
Orders Service → calls http://payments-service:8080
```

This breaks immediately in the real world:

| Problem | Why |
|---------|-----|
| Pods restart with new IPs | K8s assigns a new IP every time a container restarts |
| Horizontal scaling | You spin up 5 Payment pods — which IP do you call? |
| Rolling deployments | Old instances go down, new ones come up — addresses shift |
| Multi-environment | Dev, staging, prod all have different addresses |

**Service Discovery** solves this by making services findable by name, not by hardcoded address.

---

## What Is a Service Registry?

A **service registry** is a live database of running services and their network locations.

```
┌──────────────────────────────────────────┐
│           Service Registry               │
│  (Consul / Eureka / etcd / K8s API)      │
│                                          │
│  payments-service → [10.0.1.5:8080,      │
│                       10.0.1.9:8080,     │
│                       10.0.2.3:8080]     │
│                                          │
│  orders-service   → [10.0.3.1:8080]     │
│  users-service    → [10.0.4.2:8080]     │
└──────────────────────────────────────────┘
```

Services **register** on startup and **deregister** (or expire via TTL) on shutdown.

---

## Two Discovery Models

### 1. Client-Side Discovery

The calling service queries the registry directly and picks an instance itself.

```
  Orders Service
      │
      │ 1. "Where is payments-service?"
      ▼
  [Service Registry]
      │ 2. Returns [IP1, IP2, IP3]
      ▼
  Orders Service
      │ 3. Picks IP2 (round-robin / load balancing logic)
      ▼
  Payments Service (IP2)
```

**Examples:** Netflix Eureka (client-side), Consul with client library  
**Trade-off:** Load balancing logic lives in the client — every service must implement it

---

### 2. Server-Side Discovery

The caller sends the request to a load balancer / API gateway. The gateway queries the registry and routes for you.

```
  Orders Service
      │
      │ 1. http://payments-service/charge
      ▼
  [Load Balancer / API Gateway]
      │ 2. Queries registry → picks IP
      ▼
  Payments Service (IP chosen by gateway)
```

**Examples:** AWS ALB + ECS, Kubernetes Services, NGINX/YARP as gateway  
**Trade-off:** Extra network hop, but the client stays simple — no discovery logic needed

---

## Kubernetes — Built-in Service Discovery

K8s handles this natively via **Services** and **DNS**.

```
  ┌──────────────────────────────────────┐
  │  Kubernetes Cluster                  │
  │                                      │
  │  [Orders Pod]                        │
  │      │ calls http://payments-svc     │
  │      ▼                               │
  │  [K8s Service: payments-svc]         │
  │      │ (Virtual IP, kube-proxy)      │
  │  ┌───┴────────────────────┐          │
  │  ▼           ▼            ▼          │
  │ [Payments   [Payments   [Payments    │
  │  Pod 1]      Pod 2]      Pod 3]      │
  └──────────────────────────────────────┘
```

- Every Service gets a stable **ClusterIP** and a **DNS name** (`payments-svc.namespace.svc.cluster.local`)
- `kube-proxy` handles routing to healthy pods automatically — but it doesn't actually proxy traffic. It programs **iptables rules** on each node, so packets are redirected at the **kernel level**, not through a process. **Zero extra network hops — that's why it's fast.**
- No external registry needed — the K8s control plane IS the registry

---

## Health Checks — The Critical Ingredient

A registry is only useful if it knows which instances are **healthy**. Without health checks, you route traffic to dead services.

```
Service Registration:
  ┌──────────────────────────────────┐
  │  Register:                       │
  │    name: payments-service        │
  │    address: 10.0.1.5:8080        │
  │    health_check: GET /health     │
  │    interval: 10s                 │
  │    deregister_after: 30s         │
  └──────────────────────────────────┘

Every 10s → Registry pings GET /health
  → 200 OK  → stays registered ✅
  → Timeout / 5xx → marked unhealthy ❌ → removed after 30s
```

**Your /health endpoint should verify real dependencies:**

```
GET /health
{
  "status": "healthy",
  "db": "ok",          ← actually tested a DB query
  "cache": "ok",       ← actually pinged Redis
  "version": "1.4.2"
}
```

> A health check that just returns 200 OK without checking deps is a lie — it hides the real problem from the registry.

---

## DNS-Based Discovery

The simplest form — DNS returns multiple A records for a service name.

```
payments-service.internal → [10.0.1.5, 10.0.1.9, 10.0.2.3]

Clients round-robin across the IPs (TTL controls freshness)
```

**Problem:** DNS caches aggressively — a failed instance may stay in DNS for minutes after it dies (TTL lag).  
**Used by:** Consul DNS interface, K8s CoreDNS, AWS Route 53 private zones

---

## Consul — The Most Common External Registry

```
┌────────────────────────────────────────┐
│  Consul                                │
│                                        │
│  Agent (runs on every node/pod)        │
│    → registers local services          │
│    → runs health checks                │
│    → gossip protocol to sync cluster   │
│                                        │
│  Catalog API: GET /v1/health/service/  │
│  DNS: payments.service.consul          │
│  KV Store: config values               │
└────────────────────────────────────────┘
```

Consul also provides a **KV store** (used for feature flags, dynamic config) and **service mesh** (mTLS between services via Consul Connect).

---

## Self-Registration vs Third-Party Registration

| Model | How It Works | When To Use |
|-------|-------------|-------------|
| **Self-registration** | Service registers itself on startup | Simpler; service knows its own address |
| **Third-party** | Orchestrator (K8s) registers on behalf | Service doesn't need registry client code |

In **Kubernetes**, the platform does third-party registration — your app code never touches Consul or Eureka. The K8s Service object IS the discovery mechanism.

---

## Sidecar Pattern

### The Analogy — Motorcycle + Sidecar 🏍️

Think of a motorcycle with a sidecar attached:

```
  🏍️ + 🛺
  App     Sidecar Proxy
```

The **motorcycle (your app)** just drives — it doesn't worry about maps, tolls, or navigation.
The **sidecar** handles all that — invisibly, right beside it.

Your app code does **nothing special**. Every network call in/out is automatically intercepted by the Envoy sidecar running in the same pod.

```
  ┌─────────────────────────────────────┐
  │  Pod                                │
  │                                     │
  │  ┌──────────────┐  ┌─────────────┐  │
  │  │  Your App    │  │    Envoy    │  │
  │  │  (payments)  │  │   Sidecar   │  │
  │  │  port 8080   │  │  port 15001 │  │
  │  └──────┬───────┘  └──────┬──────┘  │
  │         │  ALL traffic    │         │
  │         └────→ intercepted│         │
  └─────────────────────────────────────┘
```

The sidecar handles transparently:
- 🔍 Service discovery (where is payments-svc?)
- ⚖️ Load balancing (which pod to pick?)
- 🔁 Retries (pod crashed? automatically try another)
- 🔐 mTLS (encrypts traffic between services automatically)
- 📊 Metrics & tracing (logs every request without touching app code)

Your app calls `http://payments-service` — the sidecar intercepts, resolves, load-balances, and retries.

---

## Service Mesh — All the Sidecars Together

A **service mesh** = every pod in the cluster gets a sidecar. Together they form a "mesh" of interconnected proxies.

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Orders   │     │Payments  │     │  Users   │
  │  App     │     │  App     │     │  App     │
  │ [Envoy]  │────▶│ [Envoy]  │────▶│ [Envoy]  │
  └──────────┘     └──────────┘     └──────────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
               [Control Plane]
               Istio / Linkerd
               (pushes config rules to ALL sidecars)
```

The **Control Plane** (Istio) pushes rules to all sidecars centrally:
- "Retry 3 times on 503"
- "Route 10% of traffic to v2 of payments (canary deploy)"
- "Encrypt everything with mTLS"

Your app never knows any of this is happening.

### Without vs With Service Mesh

| | Without Service Mesh | With Service Mesh |
|--|--|--|
| Retries | Write retry code in every service | Envoy sidecar does it automatically |
| Encryption | Configure TLS in every service | mTLS automatic between all pods |
| Tracing | Instrument every service | Sidecar captures every request |
| Discovery | App queries Consul/DNS | Sidecar handles it |

> **Service mesh moves all networking concerns OUT of your app code and INTO the infrastructure layer.**

---

## C# Angle

### K8s (Most Common) — No Client Code Needed

```csharp
// In K8s, just use the service name — DNS does the rest
builder.Services.AddHttpClient("payments", client =>
{
    client.BaseAddress = new Uri("http://payments-svc/");  // K8s DNS
});
```

No Consul SDK, no Eureka — K8s handles it.

---

### Consul with .NET (On-Prem / Multi-Cloud)

```csharp
// Register on startup
builder.Services.AddSingleton<IConsulClient>(p =>
    new ConsulClient(cfg => cfg.Address = new Uri("http://consul:8500")));

// In startup (IHostedService or minimal API startup):
var registration = new AgentServiceRegistration
{
    ID      = $"payments-{Guid.NewGuid()}",
    Name    = "payments-service",
    Address = "10.0.1.5",
    Port    = 8080,
    Check   = new AgentServiceCheck
    {
        HTTP     = "http://10.0.1.5:8080/health",
        Interval = TimeSpan.FromSeconds(10),
        DeregisterCriticalServiceAfter = TimeSpan.FromSeconds(30)
    }
};
await consul.Agent.ServiceRegister(registration);
```

---

### YARP (Yet Another Reverse Proxy) — Server-Side Discovery in .NET

```csharp
// YARP as API Gateway — reads routes from config or Consul
builder.Services.AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

// appsettings.json
{
  "ReverseProxy": {
    "Routes": {
      "payments-route": {
        "ClusterId": "payments-cluster",
        "Match": { "Path": "/payments/{**catch-all}" }
      }
    },
    "Clusters": {
      "payments-cluster": {
        "Destinations": {
          "dest1": { "Address": "http://payments-svc/" }
        }
      }
    }
  }
}
```

---

### ASP.NET Core Health Checks

```csharp
builder.Services.AddHealthChecks()
    .AddSqlServer(connectionString)   // real DB check
    .AddRedis(redisConnectionString)  // real Redis check
    .AddCheck("custom", () =>
        HealthCheckResult.Healthy("All good"));

app.MapHealthChecks("/health");
```

---

## Comparison Table

| Tool | Model | Best For |
|------|-------|----------|
| **Kubernetes Services** | Server-side, DNS | Apps running in K8s |
| **Consul** | Client or server-side | Multi-cloud, on-prem, VMs |
| **Eureka** (Netflix OSS) | Client-side | Java/Spring ecosystems |
| **AWS Cloud Map** | Server-side | AWS-native workloads |
| **etcd + custom** | Client-side | Self-managed low-level infra |
| **Istio / Linkerd** | Sidecar | K8s service mesh with observability |

---

## 🎯 Key Takeaway

> **Service Discovery is the phone book for microservices — services register by name, callers look up by name, the registry tracks live healthy instances. In Kubernetes, it's built-in via DNS + Services (use it, don't fight it). Outside K8s, Consul is the industry standard. Always back your registry with real health checks — a registry full of unhealthy entries is worse than none.**

---

## Questions to Think About

1. You have 5 Payment service pods. One crashes and is removed from the registry. A request was already in-flight to that pod. What happens, and what pattern prevents the caller from experiencing an error?
2. Your Consul health check just hits `GET /health` which always returns 200. The DB connection pool is actually exhausted. What is the impact on service discovery?
3. In K8s, you call `http://payments-svc/charge`. Walk through exactly what happens at the network layer — DNS resolution, kube-proxy, pod selection.
