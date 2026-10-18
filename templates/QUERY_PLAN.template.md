# QUERY_PLAN — <short title>

Write this *before* the SQL. Ground every row in SCHEMA.md; if SCHEMA.md doesn't say, stop and profile.

## 1. Problem

- **Business question (one sentence):**
- **Decision it informs:**
- **Unit of analysis (one row per …):**
- **Outcome / label definition:**

## 2. Business parameters

| parameter | value | note |
|---|---|---|
| population (who's in) | | |
| exclusions (test accounts, internal …) | | |
| observation window | | |
| outcome window (how long after anchor do we look) | | |
| segments | | |

## 3. Data parameters (per table)

| table | role | grain | key | time column used | window applied | why this column |
|---|---|---|---|---|---|---|
| | spine / feature / label | | | | | |

**Anchor timestamp** (the "as-of" moment each row is evaluated at):
**Rule:** every feature must be knowable at the anchor: `feature_time <= anchor`.

## 4. Assembly

- **Spine:** table + filters; defines the row count you expect.
- **Join order and cardinality:**

| step | join | cardinality | pre-aggregate? | join type | expected row count after |
|---|---|---|---|---|---|
| | | | | | |

## 5. QA assertions (must pass before any analysis)

- [ ] output grain unique on (…)
- [ ] row count equals spine count (no fan-out, no silent drop)
- [ ] no leakage: every feature time <= anchor
- [ ] null rate sane per column
- [ ] date coverage matches the intended window
- [ ] join keys normalised (case, type, whitespace)

## 6. Signal check

- **Test:** (correlation / lift by quantile / difference in means / model AUC)
- **Hypothesised direction:**
- **Result:**
- **Stable across time halves?**

## 7. If no signal: diagnostics

- [ ] date ranges and gaps
- [ ] percentiles non-degenerate
- [ ] null / zero fill
- [ ] stray predicates dropping rows
- [ ] trend break in definition
- [ ] dirty or placeholder values
- [ ] duplicates
- [ ] population too small or too homogeneous

## 8. Conclusion

- **Finding:**
- **Confidence and caveats:**
- **New facts to write back into SCHEMA.md:**
