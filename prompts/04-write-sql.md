# Prompt 04: write the structured SQL

```
The plan is approved (attached). Write the SQL as ONE query with this structure:

- `params` CTE first: every date, window length and threshold lives there.
- `spine` CTE: one row per <unit>, with the population filters; this defines the expected row count.
- One CTE per feature/label source, each pre-aggregated to the spine grain and filtered to `<= anchor` (features)
  or the outcome window (label). No raw 1:many tables joined to the spine.
- Final SELECT: LEFT JOIN from the spine; output the key, the anchor, the label, every feature, and the latest
  timestamp of each feature source (so leakage can be asserted).
- Dialect: <Snowflake | BigQuery | Postgres | …>. Use only columns present in SCHEMA.md.

After the SQL, output:
1. The exact `schemakit qa` command (key, anchor, feature-times, and an independently written --base-sql).
2. A table: each join -> cardinality -> why it cannot fan out.
3. Anything in the SQL that relies on an assumption not verified in SCHEMA.md.
```
