# Day 29: Distributed Messaging Queue System

**Date:** 2026-08-28  
**Status:** ✅ Done  
**Confidence:** 8.5/10 (solid distributed design, practical solutions)  
**Communication Level:** 8.5/10 (maintained from Phase 2)

---

## System Overview

**What:** Brand new distributed messaging queue system for SalesPoint  
**Context:** Payment processing, order fulfillment, notifications, analytics  
**Scale:**
- 100K users/tenants
- 50K transactions/sec peak
- Multiple producers (API, batch jobs, webhooks)
- Multiple consumers (payment processor, notification service, analytics)
- Multi-region (NZ/AUS)

**Message Types:**
```
Payment Queue:
  • "Charge $100 to user_123"
  • "Refund $50 to user_123"
  • CRITICAL: Ordering matters, loss not acceptable

Notification Queue:
  • "Send email to user_456"
  • "Send SMS to user_789"
  • IMPORTANT: Order doesn't matter, can tolerate delays

Analytics Queue:
  • "Log user action"
  • "Track conversion"
  • NON-CRITICAL: Order doesn't matter, loss tolerable
```

**Core Problem:** Design a messaging system that NEVER loses messages, prevents duplicate processing, maintains order when needed, and scales to 50K msg/sec.

---

## Bottlenecks Identified

### Three Critical Bottlenecks (All Equally Important)

**Bottleneck 1: Message Loss**
```
Scenario: Consumer crashes before processing
  
Naive approach:
  • Producer sends message → Message removed from queue
  • Consumer crashes → Message lost forever ❌
  
Impact: Payment never processed, customer loses money
Severity: CRITICAL ❌❌❌

Solution: Manual acknowledgment after processing
```

**Bottleneck 2: Message Duplication**
```
Scenario: Consumer processes, then crashes before acknowledging

Naive approach:
  • Consumer processes "Charge $100"
  • Consumer crashes mid-processing
  • System restarts, reprocesses same message
  • Customer charged $200 instead of $100 ❌
  
Impact: Customer overcharge, refund needed
Severity: CRITICAL ❌❌❌

Solution: Idempotency keys prevent duplicate processing
```

**Bottleneck 3: Message Ordering**
```
Scenario: Multiple messages for same tenant

Example:
  • Message 1: "Charge $100"
  • Message 2: "Refund $50"
  
If reversed:
  • Message 2 first: Refund before charge (account negative!)
  
Impact: Account balance inconsistency, wrong transactions
Severity: HIGH ⚠️⚠️

Solution: Sequence ordering with per-tenant partitioning
```

**Bottleneck 4: Scale (50K msg/sec)**
```
Scenario: Single queue, single consumer
  • 50K msg/sec → single thread bottleneck
  • Can't parallelize without losing ordering
  
Impact: Throughput not achievable
Severity: HIGH ⚠️⚠️

Solution: Partition by tenant (10 queues × 10 consumers)
```

---

## Design Decisions

### Decision 1: Technology Choice

**Choice: RabbitMQ**

```
Why RabbitMQ:
  ✓ Manual acknowledgment (prevents message loss)
  ✓ Durable queues (persist to disk)
  ✓ Message ordering guarantees (single consumer per queue)
  ✓ Dead letter exchanges (handle poison messages)
  ✓ Mature, production-grade reliability

Alternative considered:
  • Kafka: Better for logging/analytics, not ideal for transactional ordering
  • AWS SQS: Limited ordering guarantees
  • Custom queue: Too risky for fintech
```

---

### Decision 2: Message Loss Prevention (ACK Strategy)

```
Pattern: Manual Acknowledgment AFTER Processing

Flow:
  1. Producer sends message → RabbitMQ queue
  2. Consumer picks message (NOT removed from queue yet)
  3. Consumer processes: Saves to database
  4. Consumer acknowledges (message removed from queue)
  
  If crash happens before step 4:
    → Message stays in queue
    → When consumer restarts, reprocesses same message
    → Idempotency prevents double processing (see Decision 3)

Implementation:
  // Pseudo-code
  message = queue.consume()
  try {
    process_payment(message)
    save_to_database()
    queue.acknowledge(message)  ← ACK AFTER save
  } catch {
    // Don't ACK, message stays in queue
    // Consumer restart will reprocess
  }

Result: ZERO message loss ✓
```

---

### Decision 3: Duplicate Prevention (Idempotency)

```
Pattern: Idempotency Key Storage (Hybrid)

Message Header:
  {
    "idempotency_key": "payment_user123_1234567890",
    "sequence_order": 1,
    "timestamp": "2026-08-28T10:05:23Z",
    "payload": { ... }
  }

Processing Flow:
  1. Consumer receives message
  2. Extract idempotency_key
  3. Try Redis: Check if key already processed
     ├─ Found → Return cached result (no reprocessing)
     └─ Not found → Continue
  4. If Redis down, try Database
     ├─ Found → Return cached result
     └─ Not found → Process message
  5. After successful processing: Save key to both Redis + DB
  6. Set expiration:
     ├─ Redis: 30 days (hot, fast lookup)
     └─ Database: 90 days (archive, slow lookup)

Storage:
  Redis Schema:
    Key: "idempotency:payment_user123_1234567890"
    Value: { result, timestamp }
    TTL: 30 days
    
  Database Schema:
    Table: idempotency_keys
    Columns: key (PK), result, timestamp, archived
    Index: (key, timestamp)
    Retention: 90 days, then archive to S3

Cleanup:
  Worker Job (runs daily at midnight):
    SELECT * FROM idempotency_keys WHERE timestamp < 90 days ago
    Archive to S3
    DELETE from database
    
Result: ZERO duplicates ✓
```

---

### Decision 4: Message Ordering (Tenant-Based Partitioning)

```
Pattern: Partition by Tenant, Not Global

Architecture:
  Tenant_A → RabbitMQ Queue A → Consumer A
  Tenant_B → RabbitMQ Queue B → Consumer B
  Tenant_C → RabbitMQ Queue C → Consumer C
  ...
  (10 partitions for 100K tenants on average)

Sequence Ordering:
  Each tenant has independent sequence:
    Tenant_A messages: sequence 1, 2, 3, 4, ...
    Tenant_B messages: sequence 1, 2, 3, 4, ... (separate!)
    
  No global counter needed, no conflicts

Processing:
  Consumer A: Process Tenant_A messages in sequence order
  Consumer B: Process Tenant_B messages in sequence order
  
  Result: Messages for same tenant always in order ✓
          Different tenants can process in parallel ✓

Why this works:
  • Payment messages for one customer: 1→2→3 (in order)
  • Different customers: Process independently
  • Scales horizontally: Add more queues/consumers for more tenants
```

---

### Decision 5: Handling Sequence Gaps

```
Scenario: Out-of-order message arrival

Example:
  Expected: sequence 1, 2, 3
  Received: 1, 3 (missing 2)

Options:
  A) Stop and wait forever for message 2
     ❌ Blocks entire queue (bottleneck)
     
  B) Skip message 3, process later
     ❌ Out-of-order processing (consistency risk)
     
  C) Process with gap + Alert (CHOSEN)
     ✓ Keep system running
     ✓ Alert dev team for manual intervention
     ✓ Record gap in monitoring

Implementation (Option C):
  Consumer receives message with sequence gap:
    1. Check: Expected sequence = 2, Received = 3
    2. If gap detected:
       ├─ Log gap: "Gap in Tenant_A: expected 2, got 3"
       ├─ Send alert to dev team (Slack/PagerDuty)
       ├─ Hold message 3 in DLQ (Dead Letter Queue)
       └─ Continue waiting for message 2
    3. When message 2 arrives:
       ├─ Process: 2 → 3 (catch up)
       └─ Clear alert
    4. If message 2 never arrives after timeout (1 hour):
       ├─ Final alert: "Message lost, manual replay needed"
       ├─ Dev team manually replays message 2
       ├─ Process message 3 from DLQ

Result: Handles gaps gracefully, alerts ops ✓
```

---

### Decision 6: Scale to 50K msg/sec

```
Calculation:
  Total: 50K messages/sec
  Partitions: 10 RabbitMQ instances
  Per partition: 50K / 10 = 5K messages/sec
  
Single Consumer Throughput:
  Processing latency: 10ms per message
  Throughput: 1000 / 10ms = 100 messages/sec per consumer
  
Consumers needed per partition: 5K / 100 = 50 consumers
  
Total: 10 partitions × 50 consumers = 500 consumers
  
Alternative (Simpler):
  • 10 partitions (by tenant hash)
  • 10 consumers (one per partition, if lower throughput)
  • OR add more consumers per partition as needed

Deployment:
  Option 1: Kubernetes (auto-scale based on lag)
    • Horizontal pod autoscaling
    • Scale consumers based on queue depth
    
  Option 2: Fixed deployment
    • 10 RabbitMQ nodes (partition leaders)
    • Replicas for HA
    • Fixed consumer pool (500 consumers)
    
Chosen: Option 2 (Fixed, simpler for Day 29)
```

---

## Complete System Architecture

### Layer 1: Producers

```
Sources:
  • Payment API (synchronous)
  • Batch jobs (background)
  • Webhooks (from external systems)
  • Internal events (order placed, user registered)

Message Production:
  def produce_message(tenant_id, message_type, payload):
    idempotency_key = generate_key(tenant_id, payload)
    sequence = get_next_sequence(tenant_id)
    timestamp = now()
    
    message = {
      "idempotency_key": idempotency_key,
      "sequence_order": sequence,
      "timestamp": timestamp,
      "type": message_type,
      "payload": payload
    }
    
    queue_name = f"queue_tenant_{tenant_id % 10}"  // Partition by tenant
    rabbitmq.publish(queue_name, message)

Result: Message in correct queue with headers ✓
```

### Layer 2: RabbitMQ (Message Queue)

```
Configuration:
  Queues: 10 (partitioned by tenant)
    queue_tenant_0
    queue_tenant_1
    ...
    queue_tenant_9
    
  Dead Letter Exchange (DLQ):
    For messages that fail processing multiple times
    
  Durability:
    Messages persisted to disk
    Survives broker restarts
    
  Replication:
    Primary (NZ) + Replica (AUS)
    Cross-region sync every 5 minutes
```

### Layer 3: Consumers

```
Deployment: 10 consumers (1 per queue partition)
  Consumer_0 → queue_tenant_0
  Consumer_1 → queue_tenant_1
  ...
  Consumer_9 → queue_tenant_9

Processing Loop:
  while true {
    message = queue.consume()
    
    // Step 1: Check idempotency
    idempotency_key = message["idempotency_key"]
    
    if redis.exists(idempotency_key):
      cached_result = redis.get(idempotency_key)
      queue.acknowledge(message)
      continue
      
    if db.exists(idempotency_key):
      cached_result = db.get(idempotency_key)
      queue.acknowledge(message)
      continue
    
    // Step 2: Check sequence order
    expected_seq = consumer_state[message.tenant_id].next_sequence
    if message.sequence_order != expected_seq:
      ALERT("Sequence gap for tenant_" + message.tenant_id)
      hold_in_dlq(message)
      continue
    
    // Step 3: Process message
    result = process_payment(message)
    save_to_database(result)
    
    // Step 4: Store idempotency key
    redis.set(idempotency_key, result, ttl=30days)
    db.insert(idempotency_key, result, timestamp=now())
    
    // Step 5: Acknowledge
    queue.acknowledge(message)
    
    consumer_state[message.tenant_id].next_sequence += 1
  }

Latency:
  • Normal path: 50-100ms (Redis hit)
  • DB fallback: 100-200ms (Redis miss)
  • Processing: 10-50ms (DB write)
  • Total: 60-150ms per message ✓ (well below 200ms threshold)
```

### Layer 4: Idempotency Storage

```
Redis (Hot, 30-day window):
  Operation: SET idempotency:KEY result TTL=30days
  Speed: <5ms
  Used for: Recent messages (active dedup)

Database (Archive, 90-day window):
  Operation: INSERT idempotency_keys
  Speed: 10-50ms
  Used for: Fallback if Redis down + historical record

Cleanup Job (Daily, Midnight):
  SELECT * FROM idempotency_keys WHERE timestamp < 90 days
  Archive to S3 (cold storage)
  DELETE from active database
  
  Cost:
    • Redis: ~1MB for 100K keys (cheap)
    • Database: ~100GB for 90 days (archive to S3 for $1/month)
```

---

## Storage & Performance Calculations

### Message Volume

```
Peak: 50K messages/sec
Average: 25K messages/sec (typical distribution)
Per tenant: 50K / 100K tenants = 0.5 msg/sec average

Daily volume:
  50K msg/sec × 86,400 sec = 4.32 billion messages/day

Message size:
  Metadata: 500 bytes (headers)
  Payload: 1-10KB (typical)
  Total: ~5KB per message

Daily storage:
  4.32B messages × 5KB = 21.6TB/day (!!)
  
But: Messages are processed and deleted immediately
  Retention in queue: <1 hour (messages process quickly)
  Queue storage: 50K msg/sec × 3600 sec × 5KB = 900GB
```

### Idempotency Key Storage

```
Keys stored: 4.32B new messages/day
Key size: ~200 bytes (key + result hash)

Redis:
  4.32B keys × 200 bytes = 864GB
  But: 30-day retention = ~900GB (manageable for large Redis cluster)
  
Database:
  Same volume but indexed, can archive old entries
  
Cost:
  Redis: Large instance (~$500/month)
  Database: Standard instance (~$100/month)
```

---

## Bottleneck Solutions Summary

| Bottleneck | Root Cause | Solution | Trade-off |
|-----------|-----------|----------|-----------|
| **Message Loss** | Crashes before ACK | Manual ACK after DB save | Reprocessing risk (mitigated by idempotency) |
| **Message Duplication** | Consumer crash mid-process | Idempotency keys (hybrid storage) | Extra storage needed (acceptable) |
| **Message Ordering** | Global queue, parallel processing | Partition by tenant | Slight complexity in routing |
| **Sequence Gaps** | Network delays | Skip & alert dev team | Manual replay sometimes needed |
| **Scale (50K msg/sec)** | Single queue bottleneck | 10 partitions × 10 consumers | More infrastructure (acceptable) |
| **Cross-region delay** | Network latency | Replicate async (5min batch) | 1-2 second delay for cross-region |

---

## Key Design Decisions & Trade-offs

| Decision | Choice | Why | Trade-off |
|----------|--------|-----|-----------|
| **Technology** | RabbitMQ | Mature, ordering guarantees, durable | Not ideal for analytics (Kafka better) |
| **Partitioning** | By tenant (hash) | Parallelization, ordering per tenant | Slight partition imbalance possible |
| **Idempotency storage** | Hybrid (Redis + DB) | Fast primary, reliable fallback | More complex, storage overhead |
| **ACK timing** | After DB save | Prevents message loss | Slightly slower (100-150ms) |
| **Sequence gaps** | Skip & alert | Keep system running | Manual intervention sometimes needed |
| **Retention** | Messages deleted after process | Clean queue, no bloat | Can't replay old messages (design choice) |

---

## Confidence Assessment

| Aspect | Confidence |
|--------|-----------|
| **Message loss prevention** | 9/10 — ACK strategy is solid |
| **Duplicate prevention** | 9/10 — Idempotency hybrid approach sound |
| **Message ordering** | 8.5/10 — Per-tenant partitioning works well |
| **Scale design** | 8/10 — 10 partitions × 10 consumers manageable |
| **Failure handling** | 8/10 — Gap alerting practical, manual replay acceptable |
| **Storage calculations** | 7/10 — Rough estimates, needs refinement |

**Overall Day 29:** 8.5/10 ✅

---

## Learning Outcomes

### Distributed Systems Thinking
✓ Identified three critical bottlenecks (loss, duplication, ordering)  
✓ Ranked by business impact (fintech constraints)  
✓ Designed solutions for each bottleneck  

### Reliability Patterns
✓ Manual acknowledgment prevents message loss  
✓ Idempotency keys prevent duplicate processing  
✓ Partition by tenant enables ordering + parallelization  

### Scale-Aware Design
✓ Calculated throughput per consumer  
✓ Designed for 50K msg/sec (10 partitions × 10 consumers)  
✓ Storage estimates (idempotency key retention)  

### Practical Trade-offs
✓ Skip & alert for sequence gaps (pragmatic)  
✓ Hybrid idempotency storage (fast + reliable)  
✓ Accepted occasional manual replay for edge cases  

---

## Phase 2 Progress

| Day | System | Confidence | Communication |
|-----|--------|-----------|-----------------|
| Day 27 | Metrics & Monitoring | 8/10 | 8.5/10 ✅ |
| Day 28 | Twitter Feed | 8/10 | 8.5/10 ✅ |
| **Day 29** | **Messaging Queue** | **8.5/10** | **8.5/10** ✅ |

**Improving confidence while maintaining communication!** 🎯

---

## Next: Day 30 — Notification System

**What's next:** Fan-out reliability, deduplication at scale  
**Bottleneck preview:** How to notify 100K users when one event happens?

**Status:** ✅ Day 29 Complete — Ready for Day 30  
**Momentum:** Strong, applying fintech thinking to distributed systems
