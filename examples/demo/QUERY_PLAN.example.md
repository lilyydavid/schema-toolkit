# QUERY_PLAN — Which active customers will churn in the next 60 days?

Worked example on the demo warehouse (`examples/demo/`). Compare with `query_clean.sql` and `query_leaky_fanout.sql`.

## 1. Problem

- **Business question:** which currently-active customers are most likely to cancel within 60 days?
- **Decision it informs:** who customer success calls this month.
- **Unit of analysis:** one row per customer active at the anchor.
- **Outcome / label:** `churned_60d = 1` if `subscriptions.ended_at` is within (anchor, anchor + 60 days].

## 2. Business parameters

| parameter | value | note |
|---|---|---|
| population | customers with a subscription started ≤ anchor and not ended ≤ anchor | |
| exclusions | `silver_customers.is_test = 1` | SCHEMA.md §3: `test+…@acme.com` accounts |
| observation window | 30 days of events, 90 days of tickets before anchor | |
| outcome window | 60 days after anchor | |
| anchor | 2025-12-31 23:59:59 | |

## 3. Data parameters

| table | role | grain | key | time column used | window applied | why this column |
|---|---|---|---|---|---|---|
| `silver_subscriptions` | spine + label | subscription (1:1 with customer here) | `customer_id` | `started_at`, `ended_at` | active at anchor; `ended_at` in outcome window | `ended_at` is NULL while active |
| `silver_customers` | exclusion | customer | `customer_id` | n/a | n/a | filter `is_test = 0` |
| `silver_events` | feature | event | `event_id` → `customer_id` | `event_ts` | (anchor − 30d, anchor] | event time; **never** > anchor |
| `silver_tickets` | feature | ticket | `ticket_id` → `customer_id` | `opened_at` | (anchor − 90d, anchor] | |

**Anchor timestamp:** `params.anchor_ts`. **Rule:** `feature_time <= anchor`.

Known traps from SCHEMA.md that shaped the plan:
- `silver_events.customer_id` has ~3% orphans, so they drop out through the LEFT JOIN from the spine (acceptable, documented).
- `silver_events` has **no rows for 2025-08**; not inside the 30-day feature window, but would matter for a 6-month lookback.
- `silver_invoices.customer_id` is TEXT and `invoice_id` is not unique: invoices are deliberately **not** used.

## 4. Assembly

| step | join | cardinality | pre-aggregate? | join type | expected rows |
|---|---|---|---|---|---|
| spine | subscriptions ⨝ customers (is_test = 0) | 1:1 | n/a | INNER (exclusion) | 1,669 |
| + events | spine ← events | 1:many | yes: `COUNT(*)`, `MAX(event_ts)` per customer | LEFT | 1,669 |
| + tickets | spine ← tickets | 1:many | yes: `COUNT(*)`, `MAX(opened_at)` per customer | LEFT | 1,669 |

## 5. QA assertions

```bash
schemakit qa --sql examples/demo/query_clean.sql --key customer_id \
  --anchor anchor_ts --feature-times last_event_ts,last_ticket_ts --base-sql "<independent spine count>"
```

Expected: 6/6 PASS. On `query_leaky_fanout.sql`: grain_unique FAIL (1,637 duplicated keys) and no_leakage FAIL (356,444 rows).

## 6. Signal check

`schemakit signal --sql examples/demo/query_clean.sql --label churned_60d --features events_30d,tickets_90d`
Hypothesis: fewer recent events → higher churn; more recent tickets → higher churn.
Result: `events_30d` r = −0.49 (SIGNAL), `tickets_90d` r = +0.10 (SIGNAL); quintile lift is monotonic for events.

## 7. Write back to SCHEMA.md

- §7: `silver_events.event_ts` = event time, UTC; no 2025-08 data.
- §8: `silver_customers` vs `gold_customers`: canonical is `silver_customers` (gold has no `is_test`).
