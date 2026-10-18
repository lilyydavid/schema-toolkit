---
description: Answer a data question grounded in SCHEMA.md; plan, SQL, QA, signal, diagnostics
allowed-tools: [Bash(schemakit:*), Bash(python3 -m schemakit:*), Read, Write, Edit]
argument-hint: <business question>
---

Question: `$ARGUMENTS`

Read `SCHEMA.md` and `AGENTS.md` (in the schema-toolkit repo) first. Then work in these four blocks, in order. Stop after
each and wait for the user where noted.

**Mode: you do NOT have database access.** Give commands; the user runs them and pastes output.

### Block 1: What to measure
Fill `templates/QUERY_PLAN.template.md`: unit of analysis, outcome/label, population, exclusions, observation and outcome
windows, anchor timestamp. For each table you intend to use: role, grain, key, **which time column and window**
(from SCHEMA.md §7). List everything SCHEMA.md does not state, with the `schemakit` command that would establish it.
Do not fill a gap with a guess. **Stop; get the plan approved.**

### Block 2: How to source it (data assembly)
Write ONE query: `params` CTE → `spine` → one pre-aggregated CTE per source (features `<= anchor`) → final `LEFT JOIN`
from the spine. Output the key, anchor, label, features and each feature's latest timestamp. State each join's
cardinality and why it cannot fan out.

### Block 3: Does the data look right?
Give the exact `schemakit qa` command (key, anchor, feature-times, an independently written `--base-sql`). Treat any
FAIL as blocking; interpret each and give the smallest fix. Audit leakage yourself too: flag "current state" columns used
as history. Do not discuss results until every assertion passes.

### Block 4: Does it have signal? If not, why?
Give `schemakit signal --sql … --label …`. If there is no signal, do NOT conclude "no relationship": give
`schemakit diagnose …` and walk `docs/08` (date gaps, percentiles, nulls/zeros, stray predicates, trend breaks, duplicates,
power, range restriction, wrong window, segment mixing, time-split stability, negative control).

Finish by listing facts learned as proposed edits to SCHEMA.md.
