# Day 21: Case Study — Designing an Authentication System (SaaS + Fintech)

**Date:** 2026-08-13  
**Duration:** ~90 mins (comprehensive design walkthrough)  
**Status:** ✅ Complete  
**Real Application:** Multi-tenant SaaS + Fintech platform (NZ/AUS, expanding globally)

---

## Problem Statement

Design a scalable, secure authentication system for:
- **Current:** 8,000 tenants, 13,000 users
- **Target (1 year):** 20,000 tenants, 60,000+ users
- **Platform:** React frontend + .NET backend API
- **Clients:** Web, Windows desktop, Android, iOS
- **Authentication:** Currently username/password + sessions → Migrate to JWT + MFA
- **Industry:** SaaS + Fintech (high security requirements)
- **Geography:** NZ, AUS, expanding globally
- **Legacy Issues:** .NET Framework, no DI, vertical scaling, stateful application

---

## Step 1: Traffic Estimation (Critical Foundation)

### Daily User Behavior

```
Users: 60K (target)
Login pattern: 3 logins per day (log out during breaks, log back in)
Total daily logins: 60K × 3 = 180K logins/day

Login distribution: CONSISTENT throughout day
  (No peak multiplier - users spread across time zones)

Logins per second (average):
  180K logins/day ÷ 86,400 sec/day = ~2.08 logins/sec

Morning spike (8-9 AM):
  60K users log in during 1-hour window = ~16.7 logins/sec
  (This is the real peak)

Token refresh (users staying logged in):
  Assumption: 1 token refresh per hour
  60K active sessions ÷ 3,600 sec = ~16.7 refresh/sec (constant)
```

### Peak Load Calculation

```
Morning (8-9 AM - PEAK):
  Login requests: ~16.7/sec
  Refresh requests: ~16.7/sec
  Total: ~33 req/sec

Rest of day (9-5):
  Login requests: ~0.5/sec (occasional breaks)
  Refresh requests: ~16.7/sec
  Total: ~17 req/sec

Evening (5-6 PM):
  Logout spike (not critical for auth system)

Design target: Handle 33 req/sec comfortably
```

---

## Step 2: Architecture Overview

### High-Level Flow

```
┌─────────────┐
│   Client    │ (Web, Mobile, Desktop)
│ React/App   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   .NET Backend API (Load Balanced)   │
│  - Validate credentials              │
│  - Issue JWT + Refresh tokens        │
│  - Validate tokens on requests       │
└──────┬──────────────────────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│   Redis     │  │  CosmosDB    │  │ Seq (Logging)│
│  (NZ/AUS)   │  │  (Audit Log) │  │  (Monitoring)
│  Token &    │  │  (1-yr store)│  │  (Real-time) │
│  Rate Limit │  │              │  │              │
└─────────────┘  └──────────────┘  └──────────────┘
```

---

## Step 3: Token Management Strategy

### JWT Token Structure

```
Access Token (Short-lived):
  • Lifetime: 1 hour
  • Payload contains:
    {
      "user_id": 456,
      "tenant_id": "tenant_123",
      "email": "user@example.com",
      "exp": 1629398400,
      "iat": 1629394800
    }
  • Signed with secret key (can't tamper)
  • Stored in Redis for validation

Refresh Token (Long-lived):
  • Lifetime: 7 days
  • Used to get new access token
  • Also stored in Redis for revocation
  • Can be invalidated immediately on logout
```

### Token Generation

```
Login process:
  1. User enters: username + password
  2. Backend validates credentials against database
  3. Backend generates:
     - Access Token (JWT, 1 hour)
     - Refresh Token (JWT, 7 days)
  4. Store BOTH in Redis:
     Key: nz:tenant_123:user_456:access_token
     Key: nz:tenant_123:user_456:refresh_token
  5. Return both tokens to client

Client stores:
  • Access Token: In memory (for requests)
  • Refresh Token: In secure storage (localStorage on web, secure storage on mobile)
```

---

## Step 4: Multi-Tenant Isolation Strategy

### Redis Key Structure (Critical!)

```
Format: {region}:{tenant_id}:{user_id}:{token_type}

Examples:
  nz:tenant_123:user_456:access_token
  nz:tenant_123:user_456:refresh_token
  aus:tenant_789:user_111:access_token

Benefits:
  ✓ Isolation per tenant (tenant_123 data separate from tenant_789)
  ✓ Sharding per region (NZ and AUS separate Redis instances)
  ✓ Unique per user (user_456 separate from user_111)
```

### JWT Token Security

```
JWT token includes tenant_id in payload:
{
  "user_id": 456,
  "tenant_id": 123,
  "exp": 1629398400
}

JWT is SIGNED with server secret key.
If hacker tries to tamper:
  • Changes tenant_id from 123 to 999
  • JWT signature becomes INVALID
  • Server rejects the token ✓

Defense in depth:
  1. Redis lookup: {region}:{tenant_id}:{user_id}
  2. Verify tenant_id in JWT matches request
  3. Verify user_id in JWT matches request
  
If ANY mismatch → reject request
```

---

## Step 5: Complete Authentication Flows

### Flow 1: User Login

```
User Request:
  POST /api/auth/login
  {
    "username": "user@example.com",
    "password": "secure_password",
    "device_type": "mobile" or "web"
  }

Backend Processing:
  1. Hash password using Bcrypt/Argon2
  2. Compare with stored hash in database
  3. If invalid → log failed attempt, increment rate limit counter
  4. If valid:
     a. Generate access_token (JWT, 1 hour)
     b. Generate refresh_token (JWT, 7 days)
     c. Store in Redis:
        SET nz:tenant_123:user_456:access_token = <jwt>
        SET nz:tenant_123:user_456:refresh_token = <jwt>
     d. Log successful login to CosmosDB
     e. Return both tokens to client

Response:
  {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600
  }

Client Storage:
  • access_token → in memory (or sessionStorage on web)
  • refresh_token → secure storage (localStorage web, keychain mobile)
```

### Flow 2: API Request with Token Validation

```
User makes request:
  GET /api/profile
  Header: Authorization: Bearer <access_token>

Backend Validation:
  1. Extract token from Authorization header
  2. Query Redis: nz:tenant_123:user_456:access_token
  3. If Redis HIT:
     a. Token exists and is valid ✓
     b. Extract user_id, tenant_id from token
     c. Verify JWT signature (can't be tampered)
     d. Check expiration time
     e. Proceed with request ✓
  4. If Redis MISS or expired:
     a. Return 401 Unauthorized
     b. Client app receives error

Normal flow (most requests):
  ✓ Cache HIT in Redis
  ✓ Request proceeds immediately
  ✓ No DB query needed
```

### Flow 3: Token Refresh (After 1 Hour)

```
After 1 hour, access_token expires.

User makes request:
  GET /api/data
  Header: Authorization: Bearer <expired_access_token>

Backend:
  1. Check Redis: access_token is INVALID (expired) ❌
  2. Return 401 Unauthorized
  3. Client app detects 401

Client App:
  1. Detects 401 error
  2. Uses refresh_token to request new access_token:
     POST /api/auth/refresh
     {
       "refresh_token": "<refresh_token_value>"
     }

Backend Refresh Endpoint:
  1. Validate refresh_token from Redis
  2. If valid:
     a. Delete old access_token from Redis
     b. Generate NEW access_token (another 1 hour)
     c. Store new access_token in Redis
     d. Return new access_token
  3. If invalid or expired (7 days):
     a. Return 401
     b. Force user to re-login

Client:
  1. Gets new access_token
  2. Retries original request with new token ✓
```

### Flow 4: User Logout

```
User clicks: Logout button

Client Request:
  POST /api/auth/logout
  {
    "user_id": 456,
    "tenant_id": 123
  }

Backend Processing:
  1. Delete from Redis:
     DEL nz:tenant_123:user_456:access_token
     DEL nz:tenant_123:user_456:refresh_token
  2. Log logout event to CosmosDB (audit trail)
  3. Return success

Result:
  • User can NO LONGER use either token (immediate revocation) ✓
  • If attacker stole token, it's now invalid
  • User must login again to get new tokens
```

---

## Step 6: Regional Distribution (NZ/AUS)

### Data Residency Requirements

```
Compliance requirement: Data stays in region
  • NZ users → NZ Redis, NZ CosmosDB
  • AUS users → AUS Redis, AUS CosmosDB

Architecture:
┌─────────────────────────────────────┐
│   Load Balancer (Global)            │
│   Routes users to nearest region    │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐   ┌──────────┐
│ NZ      │   │ AUS      │
│ Redis   │   │ Redis    │
│ Cosmos  │   │ Cosmos   │
│ Seq     │   │ Seq      │
└─────────┘   └──────────┘

When user logs in:
  1. Load balancer identifies region (IP geolocation)
  2. Routes to regional auth service
  3. All tokens stored in regional Redis
  4. If user travels (NZ → AUS):
     - Old token still valid (can work in AUS Redis)
     - Or refresh in new region
```

---

## Step 7: Audit Logging (Fintech Compliance)

### What to Log

```
Every authentication event must be logged:

✅ IDENTITY:
   • user_id (who)
   • tenant_id (which tenant)
   • email (for quick lookup)

✅ TIMING:
   • timestamp (when)
   • timezone (user's location)
   • ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

✅ LOCATION:
   • IP address (from where)
   • Region (NZ/AUS/other)
   • Device type (mobile/web/desktop)
   • User agent (browser/app version)

✅ OUTCOME:
   • Success/Failure
   • Error code (wrong_password, account_locked, etc)
   • Failed attempt count (track bruteforce)

✅ SECURITY:
   • Was MFA used? (yes/no)
   • Session ID (for tracking)
   • Device fingerprint (for anomaly detection)

Audit Log Entry Example:
{
  "event_type": "login_attempt",
  "timestamp": "2026-08-13T14:30:45Z",
  "user_id": 456,
  "tenant_id": "tenant_123",
  "email": "user@example.com",
  "ip_address": "203.0.113.100",
  "region": "nz",
  "device_type": "mobile",
  "user_agent": "iOS/14.5 MyApp/1.2.3",
  "outcome": "success",
  "failed_attempts": 0,
  "mfa_used": false,
  "session_id": "sess_abc123xyz"
}
```

### Storage Strategy (Hybrid Approach)

```
Real-time Monitoring:
  • Tool: Seq (Azure-native log aggregation)
  • Purpose: Real-time alerting, pattern detection
  • Sends alerts for:
    - Suspicious login from unusual location
    - Multiple failed attempts
    - Bruteforce attack patterns
  
Persistent Archive:
  • Tool: CosmosDB (Azure document database)
  • Purpose: Compliance, long-term audit trail
  • Retention: 1 year (regulatory requirement for fintech)
  • Queryable by: user_id, tenant_id, date range, IP address
  
Process:
  1. Login attempt occurs
  2. Log immediately to Seq (real-time alerts)
  3. Async job: Archive to CosmosDB (persistent)
  4. After 1 year: Archive to cheap blob storage (cost optimization)

Costs:
  • Seq: ~$50-100/month (log aggregation)
  • CosmosDB: ~$100-500/month (1-year retention)
  • Blob: ~$10/month (old archive)
```

---

## Step 8: Rate Limiting (Bruteforce Protection)

### Strategy: IP + User Combination

```
Rate limiting tracks by BOTH:
  • User ID (who is trying to login)
  • IP address (from where they're trying)

Key format: "ratelimit:{user_id}:{ip_address}"

Examples:
  "ratelimit:456:203.0.113.100" = User 456 from office IP
  "ratelimit:789:203.0.113.100" = User 789 from same office IP (DIFFERENT counter)
  "ratelimit:456:192.168.1.5"   = User 456 from home IP (DIFFERENT counter)

Why this works:
  • Catches single user trying multiple passwords
  • Catches multiple users from same IP (coordinated attack)
  • But doesn't block innocent office workers if one user makes mistakes
```

### Rate Limit Rules (Differentiated by Client)

```
Mobile App Users (more careful):
  Max 5 failed login attempts per user per minute
  Then: Lock account for 15 minutes

Web Browser Users (more typos):
  Max 10 failed login attempts per user per minute
  Then: Lock account for 15 minutes
```

### Locking Strategy (Progressive)

```
Timeline:

Attempt 1-3:
  → Show error message
  → Allow retry

Attempt 4-5:
  → Still allow retry
  → But log as suspicious

After 5 failed attempts:
  → LOCK: "Too many failed attempts"
  → Temporary lock: 15 minutes
  → Send email alert: "Multiple login failures detected"

After 15 minutes:
  → Unlock automatically
  → User can retry

If 3 temporary locks in 1 hour:
  → PERMANENT lock (until email verification)
  → User must click link in email to unlock
  → This prevents bruteforce attacks
```

### Storage: Redis + Database Fallback

```
Real-time Tracking (Redis):
  Key: "ratelimit:{user_id}:{ip_address}"
  Value: failed_attempt_count
  TTL: 1 hour (auto-expire)
  
  On each failed login:
    INCR ratelimit:456:203.0.113.100
    
  On successful login:
    DEL ratelimit:456:203.0.113.100 (reset counter)

Fallback if Redis down (5-min window):
  Query database for recent failed attempts:
    SELECT COUNT(*) FROM login_audit
    WHERE user_id = 456 
    AND ip_address = '203.0.113.100'
    AND timestamp > NOW() - INTERVAL 1 HOUR
    
  If count >= 5:
    Require email verification code (slower process)
    This naturally slows down bruteforce attacks
```

---

## Step 9: Failure Scenarios & Resilience

### Scenario 1: Redis Crash (Regional)

```
What happens:
  • NZ Redis goes down
  • NZ users can't get tokens from Redis
  • Token validation fails
  • Users see "Service Unavailable" errors

Recovery Strategy (5-minute window):

Step 1: Sticky Sessions (0-5 minutes)
  • Load balancer routes same user to same backend instance
  • Token validation falls back to local verification
  • JWT signature verified locally (no Redis needed)
  • Process:
    1. User makes request with token
    2. Redis is down → MISS
    3. Fallback: Validate JWT signature locally
    4. Check token expiration locally
    5. If valid → proceed with request ✓

Step 2: Graceful Degradation
  • Rate limiting temporarily disabled (risky but acceptable)
  • Or: Rate limiting falls back to database (slower)
  • Add email verification as extra security layer
  • This slows down bruteforce attacks naturally

Step 3: Forced Re-login (after 5 minutes)
  • If Redis still down after 5 minutes
  • Force all users to logout
  • Send notification: "Service restored, please login again"
  • When Redis back online → users login normally

Downtime: ~5 minutes (acceptable for most systems)
```

### Scenario 2: Database Crash

```
What happens:
  • Credential validation fails (can't check password hash)
  • Users can't login

Recovery:
  • No good fallback (passwords stored in DB)
  • Options:
    1. Require OAuth/social login (fallback)
    2. Have read replicas for instant failover
    3. Accept downtime until DB recovers

Prevention:
  • Database replication (leader-follower, Day 19)
  • Read replicas in AUS for NZ users
  • Automated failover
```

### Scenario 3: Network Partition (NZ ↔ AUS Disconnected)

```
What happens:
  • NZ users can't reach AUS resources
  • AUS users can't reach NZ resources

Strategy:
  • Each region is self-contained
  • NZ Redis has all NZ tokens
  • AUS Redis has all AUS tokens
  • Users mostly access local region
  • Cross-region access fails gracefully
  
Acceptable for regional systems (common in distributed systems)
```

---

## Step 10: Security Best Practices

### Password Storage

```
NEVER store plain-text passwords!

Correct approach:
  1. Hash password using Bcrypt or Argon2
  2. Add salt (random, unique per password)
  3. Add pepper (secret, server-side)
  
.NET Implementation:
  using Microsoft.AspNetCore.Identity;
  
  var hasher = new PasswordHasher<User>();
  string hash = hasher.HashPassword(user, password);
  
  // Verify later
  var result = hasher.VerifyHashedPassword(user, hash, providedPassword);
```

### Token Security

```
Access Token:
  • Signed with secret key (can't tamper)
  • Short-lived (1 hour, forces refresh)
  • Stored in Redis (can be revoked immediately)
  • Contains user_id + tenant_id (immutable)

Refresh Token:
  • Also signed (can't tamper)
  • Longer-lived (7 days, reduces re-login burden)
  • Stored in Redis (can be revoked on logout)
  • More sensitive than access token
```

### CORS & Security Headers

```
CORS (Cross-Origin Resource Sharing):
  • Only allow requests from trusted origins
  • Example: https://app.mycompany.com
  
Security Headers:
  • X-Content-Type-Options: nosniff
  • X-Frame-Options: DENY
  • Content-Security-Policy: restrict script sources
  • Strict-Transport-Security: force HTTPS
```

### Client-Side Token Storage

```
Web Browser:
  • sessionStorage: Lost on browser close (secure)
  • localStorage: Persistent (but vulnerable to XSS)
  • In-memory: Fastest but lost on refresh
  
  Recommendation: sessionStorage for access token (short-lived)
                 httpOnly cookie for refresh token (prevents XSS)

Mobile App:
  • Keychain (iOS): Encrypted system storage
  • KeyStore (Android): Encrypted system storage
  • DO NOT use SharedPreferences (unencrypted)
  
Desktop App:
  • Secure credential storage (OS-specific)
  • Windows: Credential Manager
  • macOS: Keychain
  • Linux: Pass or similar
```

---

## Step 11: Monitoring & Alerting

### Key Metrics

```
Real-time Monitoring (Seq):
  • Login success rate (% successful logins)
  • Failed login attempts (detect bruteforce)
  • Token refresh rate (% of requests needing refresh)
  • Redis hit rate (should be >99%)
  • Response times (should be <100ms)

Alerts:
  • Login success rate < 90% → investigate
  • Failed attempts > 100/min from single IP → potential attack
  • Redis latency > 50ms → performance issue
  • Token refresh failures → system issue
```

### Historical Analysis (CosmosDB)

```
Weekly Reports:
  • Login counts by region
  • Failed attempt patterns
  • Unusual locations/IPs
  • Device types used
  • Response time trends

Compliance Audit:
  • Generate login reports for specific user
  • Show all access history (1-year retention)
  • Export for regulatory audits
```

---

## Step 12: Performance Optimization

### Caching Strategy

```
Layer 1: Redis Cache (first check)
  → 99% of validation requests hit Redis
  → <1ms response time
  
Layer 2: JWT Signature Validation (local)
  → Fallback if Redis miss
  → Verify signature locally
  → Still fast (<10ms)
  
Layer 3: Database (rare)
  → Only on Redis failure
  → Or for audit logging
  → Acceptable latency (10-100ms)

Result:
  • 33 req/sec peak easily handled
  • No bottleneck
  • Graceful degradation on failures
```

### Regional Latency

```
Current: NZ & AUS (close latency)
  • NZ user → NZ Redis: <5ms
  • AUS user → AUS Redis: <5ms
  • Cross-region: 20-30ms (acceptable)

Future (global expansion):
  • EU user → EU Redis: need EU region
  • US user → US Redis: need US region
  • Strategy: Multi-region Redis with region-specific writes
```

---

## Step 13: Multi-Device Session Management

### Scenario: User Logs In on Phone and Laptop

```
Phone Login:
  1. Generate access_token_phone + refresh_token_phone
  2. Store in Redis: nz:tenant_123:user_456:access_token_phone
  
Laptop Login (same user):
  1. Generate access_token_laptop + refresh_token_laptop
  2. Store in Redis: nz:tenant_123:user_456:access_token_laptop
  
Both are valid simultaneously:
  • Phone with phone token ✓
  • Laptop with laptop token ✓
  
On Logout (from phone):
  1. Delete access_token_phone + refresh_token_phone
  2. Laptop continues working (not logged out)
  
Option to logout everywhere:
  1. Delete ALL tokens for that user
  2. All devices forced to logout ✓
```

---

## Step 14: Key Design Decisions Summary

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **JWT + Refresh Tokens** | Stateless, scalable | Refresh token revocation delay |
| **Redis for tokens** | Fast validation, 99% hit | Need fallback (5-min window) |
| **Regional sharding** | Data residency, compliance | Cross-region latency |
| **IP + User rate limit** | Prevent bruteforce + DoS | Doesn't work for office scenarios alone |
| **Seq + CosmosDB logging** | Real-time alerts + audit trail | Extra infrastructure |
| **1-hour access token** | Security (limited exposure) | More refresh requests |
| **7-day refresh token** | User convenience | Larger attack window |
| **Sticky sessions fallback** | Simplicity on Redis crash | Session loss if instance crashes |
| **Email verification on lock** | Security during bruteforce | User friction |
| **1-year audit retention** | Compliance requirement | Storage cost (~100-500/mo) |

---

## Step 15: Implementation Checklist

```
Phase 1 - Core Auth (Month 1):
  ☐ JWT generation & validation
  ☐ Refresh token mechanism
  ☐ Redis token storage (regional)
  ☐ Database password hashing
  ☐ Multi-tenant isolation
  ☐ Client token storage (web/mobile)
  ☐ Basic error handling

Phase 2 - Security (Month 2):
  ☐ Rate limiting (IP + user)
  ☐ Account lockout mechanism
  ☐ Audit logging to CosmosDB
  ☐ Real-time monitoring (Seq)
  ☐ CORS & security headers
  ☐ Password reset flow
  ☐ Email verification

Phase 3 - Resilience (Month 3):
  ☐ Redis fallback strategy
  ☐ Sticky session load balancing
  ☐ Database read replicas
  ☐ Regional failover
  ☐ Circuit breaker for Redis
  ☐ Graceful degradation
  ☐ Load testing

Phase 4 - Advanced (Month 4+):
  ☐ MFA/TOTP support
  ☐ Multi-device session management
  ☐ Social login (OAuth)
  ☐ Single Sign-On (SSO)
  ☐ Advanced analytics
  ☐ Anomaly detection
```

---

## Key Takeaway

> **A production-grade authentication system balances security, performance, and reliability. Use JWT + refresh tokens for scalability. Cache tokens in Redis (99% hit rate). Implement multi-layered rate limiting to prevent bruteforce. Log everything to Seq (real-time) + CosmosDB (compliance). Plan for Redis failure with 5-minute sticky sessions. Design for multi-tenancy from day one. For fintech, security > performance.**

---

## Lessons Applied from Days 1-20

| Day | Concept | Applied |
|-----|---------|---------|
| **Day 1-2** | Horizontal scaling, load balancers | Regional load balancing (NZ/AUS) |
| **Day 3** | Caching | Redis for tokens, 99% cache hit |
| **Day 5** | CAP Theorem | Accept eventual consistency during Redis outage |
| **Day 7** | Async messaging | Async audit logging to CosmosDB |
| **Day 8** | Rate limiting | IP + user combination, progressive locking |
| **Day 18** | Database sharding | Regional sharding (NZ Redis, AUS Redis) |
| **Day 19** | Replication | Read replicas for database failover |
| **Day 20** | Case study design | Complete system thinking |

---

## Real-World Considerations for YOUR App

```
Current Issues Addressed:
  ✓ Vertical scaling → Horizontal with stateless JWT
  ✓ Stateful sessions → Stateless JWT + Redis
  ✓ No DI → Architecture ready for modern .NET
  ✓ int primary keys → Using string IDs (tenant_id, user_id)
  ✓ Reports hanging → Separate audit logging system

Future Improvements:
  → Migrate .NET Framework to .NET Core/8
  → Add DI/Dependency Injection
  → Implement MFA for fintech compliance
  → Add single sign-on (SSO)
  → Expand to global regions (EU, US)
```
