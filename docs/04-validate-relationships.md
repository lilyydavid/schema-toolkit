# 4. Validate relationships with queries, not assumptions

A foreign key that "should" exist often doesn't. Every relationship in SCHEMA.md must be *proven* once, with a date.

## The five questions per child → parent edge

1. **Cardinality.** Is the parent key unique? If not, every join duplicates rows.
2. **Match rate.** What share of non-null child keys exist in the parent?
3. **Orphans.** What are the unmatched keys (deleted parents? test data? different id space?).
4. **Null FK rate.** How many child rows have no key at all?
5. **Type & format.** `INTEGER` vs `VARCHAR`, leading zeros, case, whitespace, prefix (`cus_123` vs `123`).

## Run it

```bash
schemakit relate --child silver_events.customer_id --parent silver_customers.customer_id --write
```

```
[REVIEW] silver_events.customer_id -> silver_customers.customer_id
  cardinality : many:1
  match       : 97.02%  (orphans: 4,148, null FK: 0.0%)
  unreferenced parent keys: 5
```

`--write` records the row (with today's date) in SCHEMA.md §5.

## Decide, then write the decision down

| finding | typical decision |
|---|---|
| 100% match, many:1 | safe `INNER` join |
| 90–99.9% match | `LEFT JOIN` from the child **or** exclude orphans; state which, and what share you lose |
| < 90% match | wrong key, different id space, or a bridge table is missing; keep looking |
| parent not unique | dedupe the parent first (and note the rule), or find the true parent |
| types differ | cast explicitly on the lower-cardinality side and note it in §8 Conflicts |

## Find the *canonical* join paths

Once edges are proven, write the paths you trust in SCHEMA.md §6. Prefer paths through the spine entity
(customer) and note which edges are 1:many: those need aggregation *before* the join.

## Conflicting tables

Same concept, two tables (`silver_customers` vs `gold_customers`; `orders` vs `orders_v2`)? Compare row counts,
key overlap and a few column distributions; pick a canonical one; record it in §8 with *why*.
`schemakit lint` flags same-named tables across layers and same-named columns with different types.

Pure SQL: [`sql/03_relationships.sql`](../sql/03_relationships.sql).
