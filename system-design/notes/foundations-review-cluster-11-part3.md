# Foundations Review — Cluster 11, Part 3

**Date:** 2026-11-12
**Status:** 🔄 Cluster 11 still in progress — Q2 (Auth) closed; Q3
(Analytics) asked, paused before answering
**Previous:** `foundations-review-cluster-11.md` (Part 1),
`foundations-review-cluster-11-part2.md` (Part 2)

---

## Q2 — Auth: stolen token + Redis crash (Day 21)

**Scenario:** logout at 10:00 deletes the token from Redis; Redis crashes at
10:05; fallback = local JWT signature + expiry check; attacker uses the
stolen token at 10:06 (exp 10:50).

**Part 1 — correct:** the request succeeds. The JWT is self-contained, and
the revocation only existed in Redis.

**Misconception corrected:** "update the token's expiry on logout" is
impossible. The token lives on the client, the attacker holds a copy, and
re-signing produces a *different* token. **A stateless token can't be
revoked without server-side state.** More precisely: the token lives on the
client; what lived only in Redis was the *revocation fact*.

**Term taught (didn't know it):** **fail open** (allow when the check is
down → availability, AP) vs **fail closed** (reject → security/consistency,
CP). Cost of fail open: revoked tokens accepted until expiry. Cost of fail
closed: every user locked out for the outage. Linked back to Cluster 7, where
he correctly chose fail open for a rate limiter — low harm there.

**Short TTL + refresh token (his mitigation):** sound — it **bounds** the
window rather than closing it. The refresh token already lives in Redis
(Day 21), so during an outage refresh fails too → delayed fail closed. Cost:
more refresh traffic.

**His question — "how do I identify the attacker to fail closed?":** you
can't. Attacker and user send byte-identical, validly signed tokens; the
only distinguishing fact was in Redis. Fail closed = reject everyone,
attacker included. Use **503 + Retry-After**, not 401 — a 401 makes clients
drop tokens and stampede the login endpoint.

**His mix — fail open for known IPs/locations, closed otherwise:** a real
technique (**risk-based / adaptive authentication**), but weak as the only
factor. Token-stealing malware often runs on the victim's own machine/IP,
real users change IPs constantly, and the known-IP list needs a store that
may be down too. Stronger: **decide by the cost of being wrong** — reads
(balance/history) fail open on short-TTL tokens; money movement and account
changes fail closed; IP as an extra step-up signal.

**"Check the logs" for revocations:** right instinct (another place that
recorded the logout), wrong tool — log scans take seconds, auth needs
microseconds. Taught: **in-memory revocation denylist**. Revoked-but-unexpired
tokens are a tiny set (~5K × 40 B ≈ 200 KB vs ~1M active), fed by
`TokenRevoked` events (Outbox → broker); entries expire with the token.
Needs a `jti` claim. Costs: complexity, ms propagation window, a new
instance must load the list before serving.

**His challenge — "why not just fall back to the DB?" (good stress-test):**
framed as **cache-aside** — DB is the source of truth, Redis caches it.
Write the DB first on login; on logout, mark the token revoked in the DB,
then delete it from Redis. Settled with numbers: validation happens on
**every API request** (Day 21's 33 req/sec estimate counted only
login/refresh — a gap in those notes). 60K users × 1 req / 6 s ≈ **10K
checks/sec** of PK lookups → **verdict: no bottleneck** at Day 21 scale; his
design is simpler and better. The denylist earns its place only at ~1M+
users (170K–1.7M checks/sec), where a DB fallback would turn a Redis outage
into a full outage. Term: **thundering herd** (he said "thunderstorm").
**Lesson: the right design depends on the numbers.**

**His L1 idea — Redis → in-memory → DB:** self-corrected that per-instance
memory needs propagation (relay). Refinements: order must be
**in-memory (L1) → Redis (L2) → DB** — fastest first. Third option with no
relay: **short L1 TTL** (~10 s) — trades a 10 s revocation delay
(consistency) for no extra infrastructure (complexity). The same
propagate-vs-tolerate-staleness choice as Day 26.

---

## Q3 — Analytics: is the aggregation job really idempotent? (Day 22) — ASKED, NOT YET ANSWERED

Day 22's job: read raw_events → GROUP BY → **INSERT** aggregates → **DELETE**
raw events. Notes claim "re-run is idempotent." Questions:
1. Crash after inserting aggregates for half the links, before the delete;
   full re-run → what does the dashboard show? Actually idempotent?
2. Crash midway through the delete → what goes wrong on re-run?
3. How to make re-runs genuinely safe?

(Don't reveal the answer before he attempts it. Expected direction:
re-insert double-counts; partial delete under-counts; fix = UPSERT/replace
keyed by (link, day, …), or compute + write per day inside one transaction,
delete raw only after commit or keep raw and mark processed/watermark.
Day 22 notes need a correction afterwards.)

---

## Pattern Check

- **Strongest habit shown yet on stress-testing:** challenged *my* proposed
  mechanism (denylist) with a simpler alternative, then stress-tested his
  *own* L1 idea and found its propagation problem unprompted. This is
  exactly the gap flagged in [[assessment_weak_spots]] (Day 39) — showing
  real movement.
- **New terms needed teaching:** fail open/closed, risk-based auth,
  thundering herd, L1/L2 caching, `jti`.
- **Vocabulary** ([[vocabulary_precision_gap]]): "thunderstorm" for
  thundering herd; "token saved only in Redis" for revocation state.

---

## Still Open — next session

1. **Q3 (Analytics)** — above.
2. **Tax-rate check** (from Part 2): backfill old sales with today's tax
   rate? What should old receipts show?
3. **Saga in his past work:** which step would have needed a compensating
   action?
4. **New-instance denylist check:** an auth instance starts during a Redis
   outage with an empty denylist — risk, and what it must do first? (Less
   relevant now that the DB fallback won at this scale; optional.)
5. Then Q4: Feed (Day 23), Q5: Autocomplete (Day 24).
