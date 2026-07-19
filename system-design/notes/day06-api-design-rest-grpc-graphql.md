# Day 6 — API Design: REST vs gRPC vs GraphQL

**Date:** 2026-07-20  
**Time:** 15 minutes  

---

## The Core Question

> *"What wire protocol should this service use?"*

---

## REST (Representational State Transfer)

- **Protocol:** HTTP/1.1, JSON
- **Style:** Resource-oriented (`GET /orders/123`)
- **When to use:** Public APIs, browser clients, CRUD services
- **Strengths:** Universal, cacheable, tooling everywhere
- **Weaknesses:** Over-fetching (you get fields you don't need), under-fetching (multiple round-trips)

```
GET /users/1          → returns whole user object (maybe you only wanted name)
GET /users/1/orders   → second round-trip needed
```

---

## gRPC (Google Remote Procedure Call)

- **Protocol:** HTTP/2 + Protobuf (binary, typed)
- **Style:** Contract-first (`UserService.GetUser(userId)`)
- **When to use:** Internal service-to-service (microservices), high-throughput, streaming
- **Strengths:** ~5–10× faster than REST (binary), strongly typed contracts, bi-directional streaming
- **Weaknesses:** Not browser-friendly, steeper learning curve, harder to debug

```protobuf
rpc GetUser(UserRequest) returns (UserResponse);
```

> .NET context: gRPC is first-class in .NET via `Grpc.AspNetCore` — natural fit for C# microservices.

---

## GraphQL

- **Protocol:** HTTP, JSON (single POST to `/graphql`)
- **Style:** Client specifies *exactly* what fields it needs
- **When to use:** Complex UIs (mobile/web) with varying data needs, BFF (Backend for Frontend) layer
- **Strengths:** No over/under-fetching, one endpoint, self-documenting schema
- **Weaknesses:** Complex caching, N+1 query problem, harder rate limiting, overkill for simple APIs

```graphql
query {
  user(id: "1") {
    name          # only these fields
    orders { id } # not the whole object
  }
}
```

---

## Decision Matrix

| | REST | gRPC | GraphQL |
|---|---|---|---|
| Public API | ✅ Best | ❌ | ✅ Good |
| Microservice-to-service | ✅ OK | ✅ Best | ❌ |
| Mobile/complex UI | ⚠️ Over-fetch | ❌ | ✅ Best |
| Streaming | ❌ | ✅ Best | ⚠️ |
| CDN/HTTP Caching | ✅ Native | ❌ | ⚠️ Hard |

---

## The N+1 Problem in GraphQL

Each GraphQL field has its own **resolver function**. When resolvers run naively:

```
Query: users { orders { product { name } } }

1. Fetch all users           → SELECT * FROM users           (1 query)
2. For EACH user (say 50):   → SELECT * FROM orders WHERE user_id = ?  (50 queries)
3. For EACH order (say 200): → SELECT * FROM products WHERE id = ?     (200 queries)

Total = 1 + 50 + 200 = 251 queries! 💥
```

**The fix — DataLoader:** Batches all IDs into a single query:
```sql
SELECT * FROM products WHERE id IN (1, 2, 3, ... 200)  -- single query ✅
```

---

## CDN Caching — Why REST Wins

| Protocol | Caching |
|---|---|
| REST | `GET /products/1` → unique URL → CDN caches automatically ✅ |
| GraphQL | Everything is `POST /graphql` → CDN can't distinguish queries by URL ⚠️ |
| gRPC | Binary HTTP/2 — CDNs and proxies don't understand it natively ❌ |

---

## Real-World Architecture Pattern

The **BFF (Backend for Frontend)** pattern — used by Netflix, Airbnb, Shopify:

```
React App  ──┐
              ├──→  GraphQL BFF  ──→  gRPC (Order Service)
iOS App    ──┘                   ──→  gRPC (Inventory Service)
                                 ──→  gRPC (User Service)
```

- **GraphQL BFF** — one gateway for all frontends; each client fetches exactly what it needs
- **gRPC internally** — fast, typed, streaming between microservices
- **REST** — for third-party/public APIs that need CDN caching and broad tooling support

---

## 🎯 Key Takeaway

> **REST for public/CDN, gRPC for internal microservices, GraphQL BFF for flexible frontends — most mature systems use all three. Watch for N+1 in GraphQL; always use DataLoader.**

---

## Questions to Think About

1. In your current C# services, which internal calls could benefit most from switching to gRPC?
2. If you had a mobile app and a web app hitting the same backend, would you use a GraphQL BFF or separate REST endpoints for each? Why?
3. You have a product listing page that rarely changes — how would you cache it differently across REST, GraphQL, and gRPC?
