# 6. Grounded querying: plan first, SQL second

The failure mode of AI-written SQL is a single plausible join written from table names alone. The fix is a fixed order of work
where the model must **ground every choice in SCHEMA.md** and **write a plan you can read** before any SQL exists.

## The sequence

1. **State the problem** in one sentence: the question, the decision it informs, the unit of analysis (one row per ___).
2. **Business parameters:** population, exclusions (test accounts), observation window, outcome window, segments.
3. **Data parameters, per table:** role (spine / feature / label), grain, key, **which time column** and **which window**.
   Windows differ per table: `orders.ordered_at` is event time, `invoices.loaded_at` lags two days, `subscriptions.ended_at` is NULL while active.
4. **Anchor timestamp:** the "as-of" moment each row is judged at. Every feature must satisfy `feature_time <= anchor`.
5. **Assembly plan:** the spine, the join order, the cardinality of each join, which sides to **pre-aggregate before joining**,
   and the **expected row count after each step**.
6. **Structured SQL block:** parameters at the top (`WITH params AS (...)`), one CTE per table/role, one final SELECT.
7. **Assertions** (step 7) and **signal check** (step 8).

Use [`templates/QUERY_PLAN.template.md`](../templates/QUERY_PLAN.template.md). A worked example for the demo data is in
[`examples/demo/QUERY_PLAN.example.md`](../examples/demo/QUERY_PLAN.example.md).

## SQL conventions that make it checkable

```sql
WITH params AS (SELECT <anchor> AS anchor_ts, <horizon> AS horizon_ts),   -- every magic date lives here
spine AS (...),        -- one row per unit of analysis; defines the expected count
feat_a AS (...),       -- pre-aggregated to the spine's grain, filtered to <= anchor
feat_b AS (...),
SELECT ... FROM spine LEFT JOIN feat_a ... LEFT JOIN feat_b ...   -- LEFT from the spine, never INNER by accident
```

- Aggregate 1:many tables to the spine grain **before** joining. Never join two 1:many tables to each other through the spine.
- Output the anchor and each feature's latest timestamp so QA can assert on them.
- `COALESCE` counts to 0 only when "no rows" truly means "zero"; otherwise leave NULL and say why.

## Giving the plan to an AI

Use [`prompts/`](../prompts) (or `AGENTS.md`). The prompts instruct the model to:
read SCHEMA.md first, refuse to guess at unlisted tables/columns, produce the plan, then SQL, then the assertion commands.
