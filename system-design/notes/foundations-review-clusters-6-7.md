# Foundations Review — Clusters 6-7

**Dates:** 2026-10-02 (ad-hoc follow-up questions on Clusters 1-2), 2026-10-06
(Clusters 6-7)
**Status:** ✅ Clusters 6-7 complete, Cluster 8 next
**Format:** Cold, no notes — same as Clusters 1-5.

---

## Ad-hoc follow-ups on Clusters 1-2 (2026-10-02)

Before starting Cluster 6, several genuine follow-up questions came up from
earlier clusters — a good sign the material is being actively worked with,
not just reviewed once and left:

- **Hot-key sharding mechanism**, clarified in detail: splitting one logical
  key into N physical sub-keys isn't about running separate Redis instances —
  it's about exploiting Redis Cluster's automatic consistent hashing by
  changing the key *name*, so the same automatic system routes the N copies
  to different nodes. Correctly distinguished from cache stampede (a
  different problem — the mutex-lock fix handles the miss *moment*, hot-key
  sharding handles sustained *volume* on an already-cached key).
- **Found and fixed a real documentation gap** in `day03-caching.md`: the
  Cache-Aside pattern's write path existed in the file but was buried under
  an unrelated "Stale Data" heading, disconnected from the read-path code
  shown under Cache-Aside itself. User correctly identified this as a gap in
  the notes, not his understanding — notes were edited in place to show both
  halves together, plus a clarification distinguishing Write-around (tolerates
  staleness until TTL) from Cache-Aside's invalidate-on-write (removes
  staleness immediately). Committed separately (`ae7e4e9`).
- **CDN cache-poisoning security scenario** (a `Cache-Control: public` GET
  endpoint accidentally caching one user's sensitive account data and serving
  it to other users hitting the same URL) — walked through why this happens
  (CDN keys on URL+method only, can't distinguish callers), the correct header
  fix (`private, no-store`), and the often-forgotten remediation step: a
  header fix alone doesn't clear what's *already* cached — requires an
  explicit CDN purge (pattern-based, e.g. `/api/account/settings/*`), and
  should be treated as a security incident, not just a bug fix, since account
  data may have already leaked across users.
- Confirmed the purge mechanism generalizes across providers (not CloudFront-
  specific) — look for "Purge/Invalidate/Clear Cache" in any CDN's dashboard,
  usually wildcard-pattern-based, propagating to all edge nodes from one action.

---

## Cluster 6 — Message Queues & Event-Driven Architecture (Days 7, 14)

**Q1 (inline call vs. message queue for order-shipped email):** correctly
identified decoupling, availability, and durability as the benefits of the
queue — but initially stated them without the precise structural reason.
Sharpened to: **a non-critical side-effect (email) was wrongly coupled to the
critical path (order placement)** — exactly the Day 14 principle ("publish
events only after the critical action succeeds"). Also independently raised
the message-loss scenario (crash before the email call happens at all) and
correctly connected it, unprompted, to the **Day 38 dual-write problem** —
good unprompted cross-session transfer.

**Q2 (consumer crashes before acknowledging):** named **idempotency key**
correctly as the consumer-side fix, but initially skipped the actual queue
mechanism (why the message comes back at all). Once asked directly, correctly
described the mechanism in plain language ("message stays available until
acknowledged") but still needed the term supplied: **at-least-once delivery**
— the queue's deliberate choice to risk duplicate delivery over silent loss,
which is the direct cause of idempotency being mandatory, not optional.

**Q3 (OrderShipped processed before OrderPlaced):** mechanism was **excellent,
recalled correctly from memory with no prompting** — RabbitMQ (single ordered
queue) and Kafka (partition by entity key) both correctly named and matched
to the Day 14 lesson exactly. The *risk* framing was off ("user charged before
order confirmed" doesn't fit this scenario) — corrected to the real risk:
**effect (shipped) arriving before its cause (placed)**, which is the *exact*
causal-consistency anomaly from Day 36/Day 39 (9/10 scored there), just
surfacing in a messaging context instead of a database-replication context.
Good moment to show the same guarantee (causal consistency / consistent
prefix reads) recurring across completely different subsystems.

---

## Cluster 7 — Rate Limiting & Circuit Breakers (Days 8, 13)

**Q1 (per-merchant rate limit, horizontal scale):** correctly identified the
need for shared storage over local memory — explicit connection made back to
Cluster 1's statelessness principle this time (same root cause recognized
across clusters, improving). On the failure-mode question (Redis down —
fail open or fail closed?), **landed on the correct industry-standard answer
(fail open) but without confidence** ("not sure, but..."). Given the full
guarantee/cost reasoning for why fail-open is the standard default (a
protective mechanism failing shouldn't become a bigger outage than the thing
it protects against) — reasoning was sound, just needed the confidence
attached to it.

**Q2 (rate limiting vs. throttling vs. circuit breaker):** **clean, correct,
no corrections needed** on rate limiting (hard reject, 429) vs. throttling
(soft slowdown, delayed response). Correctly distinguished Circuit Breaker's
*direction* of protection (outbound call failures, not inbound request
volume) from rate limiting/throttling.

**Q3 (CB states + retry danger):** states correctly understood (Closed
implied, Open after N failures, limited test traffic after cooldown, close on
success/reopen on failure) — one vocabulary slip, "Semi Open" instead of
**Half-Open** (same precision pattern as scale-out/down, OAuth/JWT — now a
confirmed recurring theme across clusters, see [[vocabulary_precision_gap]]).
The retry-danger reasoning needed two guided sub-questions ("what is Open's
purpose" → "does a CB-unaware retry loop deliver that purpose or not") before
landing correctly and clearly: Open's purpose is to give the downstream
service a load-free recovery window, and retry logic that ignores circuit
state directly defeats that purpose by continuing to send load anyway.

---

## Pattern Check Against [[vocabulary_precision_gap]]

Two more instances this session (Half-Open/Semi-Open joins scale-out/down,
OAuth/JWT, N+1 misattribution) — confirms this is a stable, recurring, and
narrow pattern (precise term retrieval under cold conditions), not randomness.
Conceptual reasoning continues to be consistently strong, including multiple
instances of **unprompted cross-cluster/cross-session transfer** this round:
dual-write (Day 38) recognized in a messaging context, causal consistency
(Day 36/39) recognized in a messaging-ordering context, statelessness
(Cluster 1) recognized again in rate-limiter design.

---

## Next: Cluster 8 — Microservices & Service Discovery (Days 11-12)
