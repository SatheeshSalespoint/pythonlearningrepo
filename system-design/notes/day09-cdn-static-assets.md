# Day 9 — CDN & Static Assets

**Date:** 2026-07-24  
**Time:** 15 minutes  

---

## What is a CDN?

**Content Delivery Network** — a globally distributed network of servers that caches your content **close to the user**.

```
Without CDN:
User (Sydney) ──────────────────────► Origin Server (US East) = 200ms

With CDN:
User (Sydney) ──► CDN Edge (Sydney) ──► Origin (US East) = 8ms ✅
                       ↑ cached here
```

---

## What Gets Cached on a CDN?

| ✅ Great for CDN | ❌ Not for CDN |
|-----------------|---------------|
| Images, videos, fonts | User-specific data |
| JS/CSS bundles | Auth-protected APIs |
| HTML (static sites) | Real-time data |
| File downloads | POST/PUT requests |

**Rule of thumb:**
> If the response is the same for **every user** → CDN cache it  
> If it depends on **who is logged in** → `private, no-store`

---

## How CDN Caching Works — First vs Second Request

```
First Request (Cache MISS — always slow on day one):
User (Sydney) → CDN Edge (Sydney) → MISS → fetches from Origin (US East)
                                          → caches at Sydney edge
                                          → returns to user

Second Request onwards (Cache HIT — fast ⚡):
User (Sydney) → CDN Edge (Sydney) → HIT → returns instantly
                (never touches US origin server again)
```

> First request is always slow — CDN has nothing cached yet. Every user after that in the same region gets it fast. This is the **warm cache** concept.

---

## Do You Need to "Own" a CDN?

**Yes — you must sign up for a CDN service.** Just sending `Cache-Control` headers from your API is not enough on its own.

```
Your API sends Cache-Control: public, max-age=31536000

Without CDN:  Browser caches locally only.
              Next user in Sydney still hits your US server. ❌

With CDN:     CDN edge server caches globally.
              Next user in Sydney hits Sydney edge node. ✅
```

> `Cache-Control: public` is the **permission**.  
> CDN is the **infrastructure**.  
> You need both.

---

## Cache-Control Headers — You Control This

```http
# Public static assets — cache aggressively
Cache-Control: public, max-age=31536000, immutable

# Private user data — never cache on CDN
Cache-Control: private, no-store

# Always revalidate before serving
Cache-Control: no-cache

# Short-lived content
Cache-Control: public, max-age=300
```

| Header Value | Meaning |
|-------------|---------|
| `public` | CDN and browser allowed to cache |
| `private` | Browser only — CDN must never store |
| `no-store` | Never cache anywhere |
| `no-cache` | Cache but revalidate every time |
| `immutable` | Content will never change — skip revalidation |
| `max-age=N` | Cache for N seconds |

---

## Cache Invalidation — The Hard Problem

Files cached for 1 year — how do you deploy new versions?

### Solution: Content Hashing (Cache Busting)

```
Old:  /static/app.js           ← cached for 1 year, users see old version
New:  /static/app.abc123.js    ← new hash = new URL = fresh fetch ✅
```

Webpack, Vite, Next.js do this automatically on every build.

> Never cache files by name alone — always hash the content into the filename.  
> If you don't do this, users will see stale JS/CSS after every deployment.

---

## Pull CDN vs Push CDN

| | Pull CDN | Push CDN |
|--|----------|----------|
| **How** | CDN fetches from origin on first miss | You upload files to CDN manually |
| **Best for** | Dynamic sites, frequent changes | Large static files (videos, installers) |
| **Examples** | Cloudflare, AWS CloudFront | AWS S3 + CloudFront, Azure Blob |
| **Effort** | Near zero setup | Manual upload / CI pipeline needed |

> **Pull CDN** is the default for most web apps — just point it at your origin.

---

## Where CDN Fits in Your Architecture

```
Browser
  │
  ├──► CDN (images, JS, CSS, fonts)      ← 90% of requests served here ⚡
  │         ↓ cache miss only
  └──► Load Balancer → Your API          ← only dynamic requests reach here
```

**CDN sits in front of the load balancer** — reduces origin traffic dramatically.

---

## Azure / AWS for .NET Apps

| Service | Purpose |
|---------|---------|
| **Azure Front Door** | CDN + global load balancing + WAF |
| **Azure CDN** | Basic CDN for static assets |
| **Azure Blob Storage** | Host static assets (images, files) |
| **AWS CloudFront** | CDN in front of S3 or your API |
| **AWS S3** | Static asset storage |

```csharp
// ASP.NET Core — set cache headers for static files
app.UseStaticFiles(new StaticFileOptions {
    OnPrepareResponse = ctx => {
        ctx.Context.Response.Headers.Append(
            "Cache-Control", "public,max-age=31536000,immutable");
    }
});
```

```xml
<!-- IIS / web.config — static file caching -->
<staticContent>
  <clientCache cacheControlMode="UseMaxAge"
               cacheControlMaxAge="365.00:00:00" />
</staticContent>
```

---

## How to Detect If Your .NET App Has CDN Setup

### 1. Check Response Headers (Easiest)
Open browser → F12 → Network → click any static file:

```http
# Cloudflare
CF-Cache-Status: HIT
CF-Ray: 7a1b2c3d4e5f-SYD

# AWS CloudFront
X-Cache: Hit from cloudfront
Via: 1.1 abc123.cloudfront.net

# Azure CDN
X-Cache: TCP_HIT
X-Azure-Ref: 0abc123...

# Generic — if Age > 0, something is caching it
Age: 3456
```

### 2. Check Asset URLs in Page Source

```html
<!-- No CDN — assets from your own domain -->
<script src="/js/app.js"></script>

<!-- CDN active — assets from CDN domain -->
<script src="https://cdn.myapp.com/js/app.abc123.js"></script>
<script src="https://abc123.cloudfront.net/js/app.js"></script>
<link href="https://myapp.azureedge.net/css/app.css">
```

### 3. DNS Check

```powershell
nslookup myapp.com
# Cloudflare IPs: 104.x.x.x, 172.64.x.x
# CloudFront: shows xxx.cloudfront.net CNAME
# Azure CDN: shows xxx.azureedge.net CNAME
```

---

## Common Mistakes Senior Devs Make

| Mistake | Fix |
|---------|-----|
| Caching user-specific data on CDN | Set `Cache-Control: private, no-store` |
| No cache busting on deployments | Use content-hashed filenames |
| Forgetting CORS headers on CDN | CDN must pass through `Access-Control-Allow-Origin` |
| Caching 404 error responses | Set short TTL (max-age=10) on errors |
| Serving fonts from origin | Self-host fonts via CDN — big performance win |

---

## 🎯 Key Takeaway

> **CDN moves your content closer to users** — first request always hits origin (cache MISS), every request after that is served from the nearest edge (cache HIT). Configure `Cache-Control: public` for static assets, `private, no-store` for user data, always use content-hashed filenames for cache busting, and sign up for a CDN service (Cloudflare free tier is zero effort). A well-configured CDN serves 90%+ of traffic without touching your origin server.

---

## Questions to Think About

1. Your marketing team updates `banner.png` but keeps the same filename. Users still see the old image for days. What went wrong and what's the correct approach?
2. Your .NET API serves both public product images and private user invoices. What `Cache-Control` header would you set for each, and why?
3. Your app is getting slow for users in Asia. You add Cloudflare (pull CDN). The first user in Tokyo loads the site — what exactly happens, and when does it get fast?
