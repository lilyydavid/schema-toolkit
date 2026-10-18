# SCHEMA.md — <Company> data warehouse

> Grounding document for humans and AI. Anything not in here is a guess. Facts marked "verified" were
> checked with a query on the date shown. Regions between `<!-- schemakit:... -->` comments are
> machine-written by `schemakit`; everything else is yours.

## 1. Business model → domains

_One sentence on how the company makes money, then the 5–6 domains that explain it. See DOMAINS.md._

| domain | what it answers | anchor table(s) | entity key |
|---|---|---|---|
| customer | who is the customer | | |
| orders / usage | what they did or bought | | |
| billing | what they paid | | |
| behavior | how they used the product | | |
| support | what went wrong | | |

## 2. Architecture

- **Platform:** _(Snowflake / BigQuery / Redshift / Databricks / Postgres …)_
- **CDP / identity layer:** _(Segment, mParticle, in-house; where does the canonical customer id live?)_
- **Layers:** _raw → staging → silver (cleaned) → gold (marts) → semantic (metrics)_
- **Which layer to query from:** _(rule of thumb: highest layer that still has the grain you need)_

## 3. Conventions

- **Timezone of timestamps:** _(UTC? local? mixed per table?)_
- **Soft deletes / is_active flags:** _
- **Test / internal accounts to exclude:** _(how to identify)_
- **Currency / units:** _

## 4. Tables

### `silver_customers`
<!-- schemakit:begin silver_customers -->
- **Layer:** silver
- **Domain:** customer
- **Grain:** one row per `customer_id` — inferred (unique, no nulls) on 2026-10-18
- **Primary key:** `customer_id`
- **Row count:** 2,000
- **Time columns:** `signup_at` (2024-01-01 21:00:00 → 2025-08-23 13:00:00)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `customer_id` | INTEGER | 0.0 | 2,000 | grain, unique |
| `email` | TEXT | 0.0 | 2,000 | unique |
| `signup_at` | TIMESTAMP | 0.0 | 1,856 | time |
| `plan_tier` | TEXT | 0.0 | 6 |  |
| `is_test` | INTEGER | 0.0 | 2 |  |
<!-- schemakit:end silver_customers -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

### `silver_subscriptions`
<!-- schemakit:begin silver_subscriptions -->
- **Layer:** silver
- **Domain:** billing
- **Grain:** one row per `subscription_id` — inferred (unique, no nulls) on 2026-10-18
- **Primary key:** `subscription_id`
- **Row count:** 2,000
- **Time columns:** `started_at` (2024-01-02 09:00:00 → 2025-08-28 01:00:00); `ended_at` (2024-04-10 08:00:00 → 2026-03-01 12:00:00)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `subscription_id` | INTEGER | 0.0 | 2,000 | grain, unique |
| `customer_id` | INTEGER | 0.0 | 2,000 | unique |
| `plan` | TEXT | 0.0 | 3 |  |
| `started_at` | TIMESTAMP | 0.0 | 1,878 | time |
| `ended_at` | TIMESTAMP | 59.6 | 713 | time, sparse |
<!-- schemakit:end silver_subscriptions -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

### `silver_events`
<!-- schemakit:begin silver_events -->
- **Layer:** silver
- **Domain:** behavior
- **Grain:** one row per `event_id` — inferred (unique, no nulls) on 2026-10-18
- **Primary key:** `event_id`
- **Row count:** 139,003
- **Time columns:** `event_ts` (2024-01-03 17:33:30 → 2026-06-29 23:44:31)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `event_id` | INTEGER | 0.0 | 139,003 | grain, unique |
| `customer_id` | INTEGER | 0.0 | 2,496 |  |
| `event_type` | TEXT | 0.0 | 4 |  |
| `event_ts` | TIMESTAMP | 0.0 | 138,855 | time |
<!-- schemakit:end silver_events -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

### `silver_tickets`
<!-- schemakit:begin silver_tickets -->
- **Layer:** silver
- **Domain:** support
- **Grain:** one row per `ticket_id` — inferred (unique, no nulls) on 2026-10-18
- **Primary key:** `ticket_id`
- **Row count:** 19,331
- **Time columns:** `opened_at` (2024-01-07 09:00:00 → 2025-12-31 16:00:00)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `ticket_id` | INTEGER | 0.0 | 19,331 | grain, unique |
| `customer_id` | INTEGER | 0.0 | 1,875 |  |
| `opened_at` | TIMESTAMP | 0.0 | 10,581 | time |
| `severity` | TEXT | 0.0 | 3 |  |
| `status` | TEXT | 0.0 | 5 |  |
<!-- schemakit:end silver_tickets -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

### `gold_customers`
<!-- schemakit:begin gold_customers -->
- **Layer:** gold
- **Domain:** customer
- **Grain:** one row per `customer_id` — inferred (unique, no nulls) on 2026-10-18
- **Primary key:** `customer_id`
- **Row count:** 2,000
- **Time columns:** `updated_at` (2026-06-30 00:00:00 → 2026-06-30 00:00:00)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `customer_id` | INTEGER | 0.0 | 2,000 | grain, unique |
| `plan_tier` | TEXT | 0.0 | 3 |  |
| `lifetime_value` | REAL | 0.0 | 42 |  |
| `updated_at` | TIMESTAMP | 0.0 | 1 | time, constant |
<!-- schemakit:end gold_customers -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

### `silver_invoices`
<!-- schemakit:begin silver_invoices -->
- **Layer:** silver
- **Domain:** billing
- **Grain:** one row per `invoice_id` — VIOLATED (346 duplicate rows) on 2026-10-18
- **Primary key:** NONE (grain violated)
- **Row count:** 35,538
- **Time columns:** `invoiced_at` (2024-01-02 09:00:00 → 2026-06-29 23:00:00); `loaded_at` (2024-01-04 09:00:00 → 2026-07-01 23:00:00)
- **Profiled:** 2026-10-18

| column | type | null % | distinct | note |
|---|---|---|---|---|
| `invoice_id` | TEXT | 0.0 | 35,192 | grain |
| `subscription_id` | INTEGER | 0.0 | 2,000 |  |
| `customer_id` | TEXT | 0.0 | 2,000 |  |
| `amount` | REAL | 0.0 | 3 |  |
| `invoiced_at` | TIMESTAMP | 0.0 | 16,516 | time |
| `loaded_at` | TIMESTAMP | 0.0 | 16,516 | time |
<!-- schemakit:end silver_invoices -->

**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_

<!-- schemakit:tables-end -->

## 5. Relationships

_Child → parent, validated with `schemakit relate`. "match %" is the share of non-null child keys found in the parent._

| child (FK) | parent (PK) | cardinality | match % | orphan % | verified | notes |
|---|---|---|---|---|---|---|
| `silver_subscriptions.customer_id` | `silver_customers.customer_id` | 1:1 | 100.00% | 0.00% | 2026-10-18 | 0.0% null FK; 0 unreferenced parents |
| `silver_events.customer_id` | `silver_customers.customer_id` | many:1 | 97.02% | 2.98% | 2026-10-18 | 0.0% null FK; 5 unreferenced parents |
| `silver_tickets.customer_id` | `silver_customers.customer_id` | many:1 | 100.00% | 0.00% | 2026-10-18 | 0.0% null FK; 125 unreferenced parents |
| `silver_invoices.subscription_id` | `silver_subscriptions.subscription_id` | many:1 | 100.00% | 0.00% | 2026-10-18 | 0.0% null FK; 0 unreferenced parents |
| `silver_invoices.customer_id` | `silver_customers.customer_id` | many:1 | 100.00% | 0.00% | 2026-10-18 | 0.0% null FK; 0 unreferenced parents |
| `gold_customers.customer_id` | `silver_customers.customer_id` | 1:1 | 100.00% | 0.00% | 2026-10-18 | 0.0% null FK; 0 unreferenced parents |
<!-- schemakit:relationships-end -->

## 6. Canonical join paths

_The paths you trust. Write them once; queries reuse them._

```
customer → orders:     orders.customer_id = customers.customer_id            (many:1)
orders   → payments:   payments.order_id = orders.order_id                   (1:many — aggregate first!)
```

## 7. Time windows per table

_Different tables mean different things by "date". Fill this before writing any windowed query._

| table | event time column | load time column | typical lag | safe as-of rule |
|---|---|---|---|---|
| | | | | |

## 8. Conflicts & known traps

_Twin tables, differing definitions, columns with the same name and different meaning._

| item | conflict | canonical choice | why |
|---|---|---|---|
| | | | |
