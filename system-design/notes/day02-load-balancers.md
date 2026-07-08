# Day 2 — Load Balancers

**Date:** 2026-07-09  
**Time:** 15 minutes  

---

## What is a Load Balancer?

Sits in front of your servers and distributes incoming requests across them.

```
Client → [Load Balancer] → Server 1
                        → Server 2
                        → Server 3
```

Without it, horizontal scaling is useless — clients can only hit one IP.

---

## Load Balancing Algorithms

| Algorithm | How it works | Best for |
|---|---|---|
| **Round Robin** | Server 1 → 2 → 3 → 1 → ... | Equal servers, equal request cost |
| **Least Connections** | Send to server with fewest active requests | Long-running requests (file uploads) |
| **IP Hash** | Same client IP → always same server | When you *need* stickiness |
| **Weighted** | Server 1 gets 60%, Server 2 gets 40% | Mixed server sizes |

---

## Health Checks

Load balancers ping each server every few seconds (e.g. `GET /health`).  
If a server fails → automatically removed from the pool.  
When it recovers → added back. Zero manual intervention.

```
LB pings → Server 2 returns 500 repeatedly
LB removes Server 2 from rotation
Traffic now only goes to Server 1 & 3
```

> ⚠️ `/health` must check real dependencies (DB, Redis, 3rd party) — not just return 200.  
> A fake 200 means the LB never removes a broken server → users hit errors.

---

## L4 vs L7 Load Balancers

| | **L4 (Transport)** | **L7 (Application)** |
|---|---|---|
| Operates on | TCP/UDP (IP + Port) | HTTP (URL, headers, cookies) |
| Speed | Faster | Slightly slower |
| Smart routing? | ❌ No | ✅ Yes |
| Example | AWS NLB | AWS ALB, nginx |

**L7 example:** Route `/api/images/*` to image servers, `/api/auth/*` to auth servers — same load balancer.

---

## The Sticky Session Trap ⚠️

Sticky sessions = same user always hits same server.

```
❌ Problem: secretly stateful
   Server goes down → all its users lose their session
   Defeats fault tolerance — hidden single point of failure
```

> **Rule:** Never use sticky sessions as a shortcut. Fix the app to be stateless (Redis) instead.

---

## C# / Azure Context

- **Application Gateway** = L7 load balancer for ASP.NET apps in Azure
- Handles SSL termination — your servers receive plain HTTP internally

```
HTTPS (client) → [App Gateway - SSL termination] → HTTP (internal servers)
```

---

## 🎯 Key Takeaway

> **A load balancer is only as good as your health checks and stateless design.**  
> Fake health checks hide broken servers. Sticky sessions hide stateful apps.  
> Fix both, and horizontal scaling becomes truly fault-tolerant.

---

## Questions to think about

1. Does your current C# API have a `/health` endpoint? Does it check the DB?
2. If your load balancer removed one server right now — would any users lose their session?
3. Which algorithm would you pick for your current app, and why?
