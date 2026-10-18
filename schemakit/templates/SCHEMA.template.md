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

<!-- schemakit:tables-end -->

## 5. Relationships

_Child → parent, validated with `schemakit relate`. "match %" is the share of non-null child keys found in the parent._

| child (FK) | parent (PK) | cardinality | match % | orphan % | verified | notes |
|---|---|---|---|---|---|---|
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
