# Day 30: Case Study — Notification System (Multi-Channel Delivery)

**Date:** 2026-08-31  
**Duration:** ~45 mins  
**Status:** 🔄 In Progress (Design foundation complete, refinement pending)  
**Difficulty:** Medium → Hard (Phase 3 transition)  
**Confidence Level:** 8.5/10 (strong architecture decisions)  
**Communication Level:** 8/10 (improving clarity and structure)

---

## The Challenge

Design a **multi-channel notification system** that reliably delivers messages to users through email, SMS, and push notifications with guaranteed delivery and proper handling at scale.

**User Experience:**
```
Event: Payment processed
  ↓
System detects event
  ↓
Send notifications:
  • Email to user
  • SMS to user
  • Push notification to mobile app
  ↓
User receives all 3 within 1-2 seconds
```

**Key Requirements:**
- Reliable delivery (messages never lost)
- Multi-channel support (email, SMS, push, webhooks)
- Low latency (<2 seconds preferred)
- No duplicate delivery
- Scale: 100K users across regions (NZ/AUS), up to 3M+ notifications/day

---

## Scale Estimation

### Regional Distribution

```
Total Users: 100K
  • NZ region: 60K users
  • AUS region: 40K users
```

### Daily Notification Volume

```
Assumptions:
  • Average notifications per user: 50/day
  • Includes: payments, reports, alerts, OTP

NZ Region:
  • 60K users × 50 notifications/day = 3M notifications/day
  • Average: 3M ÷ 86,400 sec = 34.72 req/sec
  • Peak (100x multiplier): 3,472 req/sec

AUS Region:
  • 40K users × 50 notifications/day = 2M notifications/day
  • Average: 2M ÷ 86,400 sec = 23.14 req/sec
  • Peak (100x multiplier): 2,314 req/sec

Cross-region (webhooks, admin alerts):
  • 10% of peak traffic = 347 req/sec

TOTAL PEAK: 3,472 + 2,314 + 347 = 6,133 messages/sec
```

### Peak Multiplier Reasoning

```
Why 100x multiplier?

Scenario 1: Time-of-day spike
  • Morning (8 AM): Users check notifications
  • Evening (6 PM): Report generation, alerts
  • Multiplier: 4x

Scenario 2: Business events
  • End-of-day settlements
  • Batch reports generated
  • Multiplier: 15x

Scenario 3: System recovery
  • Service restart, backlog notifications
  • Multiplier: 75x

Worst case: 4 × 15 × 2 = ~120x (use 100x as reasonable estimate)
```

---

## Bottleneck Analysis

### Critical Bottlenecks (By Business Impact)

**Bottleneck 1: Message Loss (CRITICAL ⚠️⚠️⚠️)**

```
Problem:
  If database crashes, notification messages lost
  Customer doesn't receive payment confirmation
  
Impact:
  • Customer confusion ("Did my payment go through?")
  • Support tickets
  • Business trust erosion

Solution:
  • Database replication (primary + replica)
  • RabbitMQ persistence (messages in queue survive broker restart)
  • Failover: Promote follower to leader
  • Acceptable latency: 30-60 seconds during failover
```

**Bottleneck 2: Slow Delivery Channels (HIGH ⚠️⚠️)**

```
Problem:
  Different channels have different speeds:
  • Email: 100-500ms per message (SLOW)
  • SMS: 1-2 seconds per message (SLOWER)
  • Push: 50-200ms (FAST)
  
If one channel blocks others:
  • SMS slow → all notifications delayed?
  • User waits for SMS while email queued?
  
Impact:
  • Latency SLA violated (>2 seconds)
  • Poor user experience

Solution:
  • 3 independent services (Email, SMS, Push)
  • Each scaled independently
  • Non-blocking: If SMS slow, email still sends
```

**Bottleneck 3: Service Failures (HIGH ⚠️⚠️)**

```
Problem:
  Consumer crashes, RabbitMQ down, network issues
  Messages not delivered, no persistence
  
Impact:
  • Brief delivery delay (acceptable)
  • No message loss (if queue persistent)

Solution:
  • RabbitMQ durability (persist to disk)
  • Multiple consumers (parallel processing)
  • Automatic failover
```

**Bottleneck 4: Network Issues (MEDIUM ⚠️)**

```
Problem:
  SMS provider down, email service unavailable
  Network timeouts, carrier routing failures
  
Impact:
  • Temporary delivery failure
  • Solvable with retry + backoff

Solution:
  • Retry strategy with exponential backoff
  • Circuit breaker pattern
  • DLQ for persistent failures
```

---

## Architecture Decision: 3 Independent Services

### Why Split Instead of Monolithic?

```
BEFORE (Bad - Monolithic):
  RabbitMQ → Single Notification Service → Email/SMS/Push
             (If SMS slow, ALL blocked) ❌

AFTER (Good - Microservices):
  RabbitMQ → Email Service (scaled independently)
           → SMS Service (scaled independently)
           → Push Service (scaled independently)

Benefits:
  ✅ Email delay doesn't block SMS
  ✅ SMS bottleneck fixed independently
  ✅ Each service handles own failures
  ✅ Independent scaling per channel
```

---

## Hybrid Channel Strategy

### Critical vs Non-Critical Notifications

```
CRITICAL (Payment, OTP, Auth):
  Send: Email + SMS + Push
  Why: User MUST receive, multiple fallbacks
  Retry: Aggressive (72 attempts in 24 hours)

NON-CRITICAL (Reports, Digest, Marketing):
  Send: Email only
  Why: Non-urgent, saves cost and load
  Retry: Moderate (5 attempts in 2 hours)

OTP Special Case:
  Primary: SMS (fastest for user action)
  Fallback: Email (if SMS fails after retries)
  Retry: SMS-focused, email as backup
```

---

## Service Designs

### Email Service Flow

```
INPUT: Notification message from RabbitMQ
  {
    "notification_id": "payment_123456",
    "type": "PAYMENT",
    "user_id": "user_abc",
    "channels": ["email", "sms", "push"],
    "data": { "amount": 100, "merchant": "XYZ", ... }
  }

PROCESS:
  Step 1: Extract email address from database
          SELECT email FROM users WHERE user_id = "user_abc"
          
  Step 2: Cache user profile details in Redis
          (Optimize for next request)
          
  Step 3: Build email content
          Subject: "Payment Confirmation - $100"
          Body: "You paid $100 to XYZ at 10:05 AM"
          
  Step 4: Send via email provider (SendGrid/SES)
          
  Step 5: Track delivery result
          If success: Log confirmation
          If fail: Trigger retry logic
          
  Step 6: Update status in database
          INSERT notification_history 
          {notification_id, channel="email", status="sent", timestamp}

OUTPUT: Email sent confirmation
```

### SMS Service Flow

```
INPUT: Notification message from RabbitMQ

PROCESS:
  Step 1: Get message from RabbitMQ queue
          Consume and acknowledge
          
  Step 2: Retrieve phone number from Redis
          (User profile cached for speed)
          
  Step 3: Build SMS content
          "Payment confirmed: $100 to XYZ"
          
  Step 4: Send via SMS provider (Twilio/AWS SNS)
          
  Step 5: Track delivery result
          Verify carrier confirmation
          
  Step 6: Update status in database
          INSERT notification_history

OUTPUT: SMS sent confirmation
```

### Push Notification Service Flow

```
INPUT: Notification message from RabbitMQ

PROCESS:
  Step 1: Get message from RabbitMQ
  
  Step 2: Retrieve device tokens from Redis
          (User's mobile app registration)
          
  Step 3: Build push payload
          Title: "Payment Confirmed"
          Body: "$100 paid to XYZ"
          
  Step 4: Send to push provider (Firebase/APNs)
          
  Step 5: Track delivery result
          Device online? Notification received?
          
  Step 6: Update status in database

OUTPUT: Push sent confirmation
```

---

## Retry + Dead Letter Queue (DLQ) Strategy

### Retry Policy

```
Retry Schedule:

  PHASE 1 (Immediate Backoff - First Hour):
    Attempt 1: T+0 (immediate)
    Attempt 2: T+1 second
    Attempt 3: T+2 seconds
    Attempt 4: T+6 seconds (exponential: 1s → 2s → 6s)
    
  PHASE 2 (Hourly Retries - 24 Hours):
    After 1 hour, retry every 60 minutes
    Attempt 5: T+1 hour
    Attempt 6: T+2 hours
    Attempt 7: T+3 hours
    ...
    Attempt 28: T+24 hours
    
  Total Attempts: 4 (immediate) + 24 (hourly) = 28 attempts per message
  Time span: 24 hours
  
  Then: Move to DLQ
```

### DLQ Handling

```
When Message Goes to DLQ:
  • After 24 hours and all 28 retries failed
  • OR on permanent error:
    - Invalid phone number (SMS)
    - Invalid email format (Email)
    - User deleted/blocked (Push)

DLQ Processing:
  Step 1: Create alert to infrastructure team
          Send to Slack/PagerDuty
          Include: notification_id, failure reason, user_id
          
  Step 2: Store in DLQ table for investigation
          TABLE: dlq_messages
          Columns: id, notification_id, service, error, timestamp
          
  Step 3: Manual replay capability
          Ops team can:
          • Fix underlying issue
          • Manually replay message
          • Investigate root cause
          
  Step 4: Archive after 30 days
          Move to cold storage (S3/Blob)
          Keep for compliance/audit
          Delete from active DLQ
```

### DLQ Monitoring

```
Alert Conditions:
  • DLQ messages > 100 in 5 minutes (spike)
  • Same notification_id in DLQ (duplicate issue)
  • Same user_id in DLQ > 5 messages (user data issue)
  
Actions:
  • Alert ops team immediately
  • Check service health
  • Check provider status (SendGrid, Twilio, etc.)
  • Investigate root cause
```

---

## Complete System Flow

### Happy Path (Payment Notification)

```
1. Payment processed in payments service
   → Event: "payment.completed"
   
2. Write notification message to database
   INSERT notifications 
   {user_id, type="PAYMENT", channels=["email","sms","push"]}
   
3. Async worker publishes to RabbitMQ
   3 separate messages to 3 queues:
   - queue_email
   - queue_sms
   - queue_push
   
4. Three services consume independently
   Email Service → SendGrid → User's inbox
   SMS Service → Twilio → User's phone
   Push Service → Firebase → User's app
   
5. Each service updates status
   notification_history table updated
   
6. User receives all 3 within 1-2 seconds ✓
```

### Failure Path (SMS Provider Down)

```
1. SMS service tries to send via Twilio
   → Twilio returns error (service down)
   
2. Immediate retry (1s, 2s, 6s exponential)
   Still failing
   
3. Enter hourly retry phase
   Retry every 60 minutes for 24 hours
   
4. Meantime:
   Email still sends (independent) ✓
   Push still sends (independent) ✓
   
5. After 24 hours if SMS still failing:
   Move to DLQ
   Alert ops: "SMS service issue for notification_123"
   
6. Ops investigates:
   "Twilio account out of credits"
   Fixes account
   Manual replay message
   SMS sent ✓
```

---

## Key Design Decisions

| Decision | Choice | Why | Trade-off |
|----------|--------|-----|-----------|
| **Services** | 3 independent | Avoid blocking, scale independently | More infrastructure |
| **Channel strategy** | Hybrid (critical=all, non-critical=email) | Cost + reliability balance | Complex routing logic |
| **Retry count** | 28 attempts over 24 hours | Aggressive for fintech | Higher load on providers |
| **Backoff strategy** | Exponential then hourly | Balance speed + resilience | Complex to implement |
| **DLQ timeout** | 24 hours | User impact acceptable | Delayed problem visibility |
| **Redis caching** | User profile details | Reduce DB queries | Cache invalidation needed |

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Scale estimation** | 9/10 — Regional breakdown clear |
| **Bottleneck identification** | 8.5/10 — Ranked by business impact |
| **Service separation** | 9/10 — Hybrid approach solid |
| **Retry strategy** | 8/10 — Reasonable, needs refinement |
| **DLQ handling** | 8/10 — Good alerting, needs ops runbook |
| **Multi-region design** | 7/10 — Basic, needs sync strategy |

**Overall Day 30:** 8.5/10 ✅

---

## What Still Needs Refinement (Day 31)

```
PENDING DETAILS:

1. Multi-region Synchronization
   Q: How do NZ and AUS services sync?
   Q: If NZ consumer fails, does AUS service retry?
   Q: Data consistency across regions?

2. Idempotency & Deduplication
   Q: What if message processed twice?
   Q: How to prevent duplicate notifications?
   Q: Use idempotency keys like Day 29?

3. Rate Limiting Per User
   Q: If user gets 100 notifications/second?
   Q: Throttle? Queue? Drop?
   Q: Prevent notification spam?

4. Provider Cost Optimization
   Q: Email = free, SMS = $0.01 each
   Q: How to optimize spend?
   Q: DLQ messages = wasted cost?

5. Monitoring & Observability
   Q: How to track end-to-end delivery?
   Q: Dashboard for ops team?
   Q: Alert on high failure rate?

6. Database Schema Details
   Q: What columns in notification_history?
   Q: Indexing strategy?
   Q: Retention policy?
```

---

## Communication Progress

**Starting:** 8.5/10 (from Day 29)  
**Current:** 8/10 (slight dip due to new concepts, expected)

### What Improved ✓
- Clear bottleneck ranking (by business impact)
- Concrete service examples
- Structured retry strategy

### What Needs Polish ⚠️
- Grammar: "It would tried" → "it would be tried"
- Redundancy: Avoid template-filling (step 3 and 4 same)
- Clarity: Explain reasoning before solutions

### Coaching for Day 31
- Same answer format (Problem → Solution → Tradeoff)
- Add "Why this is important" before each design choice
- Use concrete numbers (72 retries, not just "many")

---

## Learning Outcomes

### Distributed Systems Thinking
✓ Identified 4 critical bottlenecks  
✓ Ranked by business impact (not just technical)  
✓ Understood fintech priorities (loss > latency)  

### Multi-Channel Architecture
✓ Service separation prevents blocking  
✓ Independent scaling per channel  
✓ Hybrid strategy balances cost + reliability  

### Reliability Patterns
✓ Retry with exponential backoff  
✓ DLQ for persistent failures  
✓ Alert system for ops visibility  

### Production-Grade Thinking
✓ User profile caching (Redis optimization)  
✓ Failure handling with graceful degradation  
✓ Archive strategy for compliance  

---

## Next: Day 31 Refinement

**Focus Areas:**
1. Multi-region synchronization
2. Idempotency & deduplication (apply Day 29 patterns)
3. Rate limiting per user
4. Database schema design
5. Monitoring & observability

**Status:** ✅ Foundation solid, ready to build on it!

