# Day 38: Applied Session — Xe Rate Alerts, Production Design

**Date:** 2026-09-16
**Duration:** ~90 mins
**Status:** ✅ Complete — not on the roadmap
**Phase:** 2.5 Bridge (Days 36–41) — substituted for the planned Day 38 slot
**Difficulty:** Medium (familiar shape — write bottleneck, decoupled delivery)
**Confidence:** 7/10

**Note:** the Day 35 bridge plan scheduled the consistency re-test for today.
That's now **Day 39**, moved back one slot. This session used the time instead
to scale a real project — the take-home at
[`xe-hiring-takehome`](../../Xe/xe-hiring-takehome-csharp-vue/xe-hiring-takehome) —
from a single-tab in-memory tool to a production design. Same underlying skill
(guarantee → mechanism → cost, capacity vs availability), different material.

---

## The Source Project

A rate-alert feature built for a hiring take-home: fetch live FX rates from the
Xe Currency Data API, let a user set a threshold on a currency pair, and surface
when it's crossed.

**As it exists today** ([NOTES.md](../../Xe/xe-hiring-takehome-csharp-vue/xe-hiring-takehome/NOTES.md)):
- Alerts live in a `ConcurrentDictionary` — in-memory, gone on restart
- Evaluation happens **on read** (`GET /api/alerts` triggers `AlertEvaluator.Evaluate`)
- `Triggered`/`TriggeredAt` latches on first crossing and never clears — a
  computed flag would flap on a volatile day and lose the fact that it ever fired
- No notification service — a user only finds out by opening the app

The take-home's own "What I'd do next" list already named the target: persist
alerts, move evaluation to a background worker, add notifications via an outbox.
This session designed that version properly instead of leaving it as a bullet list.

---

## The Brief

> 10,000 users, 5 alerts each (50,000 alerts), ~200 distinct currency pairs,
> rates refreshed every 5 seconds. A user must be notified within a few seconds
> of a real crossing — a push notification, not "next time they open the app."
> Alerts must survive a restart. Assume a bad day: 5% of all alerts cross in the
> same minute (a market shock).

---

## Scale — the numbers, and where they went wrong first

| Stage | Steady-state | Peak (bad minute) |
|---|---|---|
| Ingestion (Xe API) | 40 req/sec (200 pairs / 5s) | same |
| Evaluation (in-memory, CPU) | 10,000/sec (50,000 alerts / 5s) | same |
| Writes (DB) | ~25/sec (assumption: 1% of peak) | 2,500 crossings in one 5s tick |
| Notifications | ~0 | 500/sec |

**Errors made and self-corrected on the way to this table:**

1. **Conflated "evaluated" with "written."** First pass called all 10,000
   evaluations/sec "writes." Evaluation is a pure function reading a cached
   rate — no I/O. A write only happens when state actually *changes* (a
   crossing). Confusing the two would have led to provisioning DB write
   capacity for a load that was actually CPU-only.

2. **Proposed per-user DB reads, then caught it unprompted.** Floated fetching
   alerts with one query per user (10,000 queries/cycle = 2,000/sec) instead of
   one batched `SELECT * FROM alerts`. Recognised mid-session that this was
   *the same batching-gap mistake* just diagnosed on the write side, just moved
   to the read side. Correct read design: **1 batched query per tick**,
   regardless of how many users own the rows.

3. **Asserted numbers without derivation** ("10x during peak", "1M req/sec to
   DB") — walked back to arithmetic each time. Same "write out the zeros"
   habit flagged since Day 22/33, still needs conscious effort under pressure.

4. **Confused a query-count observation with a rate ratio.** "1 batched read
   vs. up to 2,500 individual writes" is a real and useful asymmetry — but it's
   a **batching gap per cycle**, not a "read:write ratio" in the requests/sec
   sense. Forcing it into that shape produced a meaningless number
   ("1:2500"); naming it correctly pointed straight at the fix (batch the
   writes too).

---

## Bottleneck — the real relapse of the day

Asked: *"which stage breaks first under this load — nothing has failed, what
saturates?"*

Answered: *"writes, because if the DB goes down, replicas take time to
recover."*

**Same conflation as Day 35 Round 3.** The question was about **capacity**
(what breaks while everything is healthy); the answer was about
**availability** (what if something dies). Corrected in-turn once named
explicitly as two different question modes — but the fact it resurfaced,
unprompted, on a fresh scenario is the actual finding of the day. This is not
a knowledge gap; it's a reflex under pressure, and it needs a mechanical
tell to interrupt it (see Key Takeaway below).

### The actual mechanism, once reframed around capacity

```
Ingestion    → in-house HTTP call, ~40/sec                         → fine
Evaluation   → in-memory comparison, no network, 10,000/sec        → fine
Writes       → own DB, ~1-5ms round trip, batchable                → tight, survivable
Notifications → THIRD-PARTY provider, ~100-300ms, NOT batchable,
                and you don't control its latency or limits        → breaks
```

**Worked example:** a naive worker that sends 500 notifications sequentially,
waiting for each response, at 200ms average provider latency:

```
500 × 200ms = 100,000ms = 100 seconds, inside a 5-second tick budget.
```

The tick doesn't crash — it just runs long, and the backlog compounds every
cycle after. No error anywhere. This is the same "breaks at 3am, silently"
shape as the compaction discussion from Day 33's notes.

**Tested and rejected: does lengthening the tick (5s → 10s) fix this?** No —
it doesn't reduce total notification work, it concentrates it (fewer, bigger
batches: ~416/tick instead of ~208/tick), while *also* doubling worst-case
detection latency for a guarantee that promised "a few seconds." A fix has to
be structural (decouple delivery from the tick), not a schedule knob, because
the bottleneck was never about frequency — it was about a fixed amount of
blocking work that doesn't shrink no matter how it's grouped.

---

## Design — three notification architectures, compared

| | Mechanism | Cost |
|---|---|---|
| **Case 1** | Eval worker writes only to an outbox table; a worker process polls it and sends, async | +1 table, +1 process, +monitoring. No broker at all. |
| **Case 2** | Eval worker writes `TriggeredAt` to DB **and** publishes to a broker, as two separate calls | **Dual-write problem**: DB commit can succeed while the publish silently fails — DB says triggered, nobody was ever told, and there's no record it should have happened. Also: if the broker stalls, the eval worker blocks, coupling evaluation latency to broker health. |
| **Case 3** | Eval worker writes alert + outbox row **in one transaction**; a separate relay drains the outbox to a broker; a notification service consumes and sends | +2 components (outbox, broker) to operate. **No dual-write** — the eval worker makes exactly one write, in the critical path; the relay retries indefinitely without risk, because a `pending` outbox row is a durable record that delivery still needs to happen. |

**Recommendation: Case 3**, justified by scale (500/sec peak justifies the
extra infra; a single-process worker pool wouldn't survive a real broker-scale
fanout) — not "most robust by default."

**Correction applied to the final guarantee statement:** first draft claimed
"message delivered within 5 seconds." Nothing in the design bounds that — the
relay poll interval, broker capacity, and notify-service throughput are all
unspecified, and the number was asserted, not derived (same pattern as the
scale-estimation errors above). The design's actual, defensible guarantee:

> **At-least-once delivery, no silent loss**, decoupled from the evaluation
> tick — the broker guarantees at-least-once, and idempotency key
> `(alertId, triggeredAt)` makes it effectively-once at the consumer.

Latency is a secondary property of this design (typically fast, occasionally
delayed under load), not a bound it was built to enforce. Naming *which*
guarantee a mechanism actually produces — durability here, not speed — is the
same discipline as Day 33's "derive from text, don't guess a multiplier."

---

## Final Answer (interview-shaped)

> Replace in-memory storage with a DB — alerts and their state live there,
> survive restart. A background processor, on a timer, fetches all active
> alerts in **one batched query** (not per-user), evaluates them against
> rates cached from the Xe API (dedup by pair, batch by base currency, 20s
> TTL — validated in the actual take-home), and writes state changes back in
> **one batched update**, not per-row round-trips. The same transaction that
> latches a crossing writes a row to an outbox table. A relay drains the
> outbox to a message broker; a separate notification service consumes and
> sends, keyed by `(alertId, triggeredAt)` for idempotency.
>
> **Guarantee:** at-least-once, no-silent-loss notification delivery,
> decoupled from the evaluation tick.
> **Mechanism:** transactional outbox + relay + broker + idempotent consumer.
> **Cost:** two additional components (outbox, broker) and their monitoring —
> justified once notification volume outgrows a single in-process worker pool;
> at 10K users / 500 peak notifications/sec, it does.

---

## Key Takeaways

1. **"What breaks under load" and "what if it fails" are different questions.**
   The tell that they've been conflated: the answer starts with "if X goes
   down." Watch for that phrase specifically — it's the mechanical signal
   that the reflex has fired again, even after Day 36's teaching landed.

2. **The bottleneck is rarely raw throughput — it's a blocking call to
   something you don't control, done one-at-a-time inside a fixed budget.**
   CPU-only stages essentially never break at these scales. It's always the
   network hop outside your own walls.

3. **Slowing a schedule only fixes a problem caused by frequency.** If the
   total amount of work doesn't shrink when you space it out, the interval
   was never the lever — ask "does the total work change, or just how it's
   grouped?" before proposing a timing fix.

4. **A design pattern meant to prevent a failure mode isn't automatically an
   instance of it.** Outbox + relay was mislabeled as having the dual-write
   problem it exists to solve — the tell was not re-deriving *why* the
   pattern works (one write, in one transaction) before assigning it a cost.

5. **State which guarantee a mechanism actually produces, not the one that
   sounds reassuring.** At-least-once + idempotency ≠ a latency bound. If
   nothing in the design traces back to a number, the number is a hope, not
   a guarantee.

---

## Next: Day 39 — Consistency Re-Test (moved from today)

Closed notes. Round 3 re-run (merchant refund / follower lag / read-your-own-writes
vs monotonic reads), plus two new scenarios. Gate: ≥8/10 to reopen Phase 3 on Day 42.
