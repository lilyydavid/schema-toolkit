# 8. Is there signal? And if not, why not?

Only after QA passes: does the data say anything about the business problem?

## Step A: signal check

```bash
schemakit signal --sql query.sql --label churned_60d --features events_30d,tickets_90d --time-col observed_at
```

`--time-col` should vary across rows (e.g. each row's observation date). With a single fixed anchor, leave it off.

Per feature you get: coverage, correlation `r` with the label, a **permutation p-value** (shuffle the label, how often
does chance beat the observed |r|?), a **time-half stability** check (does the sign hold in both halves?) and **quantile
lift** (label mean by feature quintile) to reveal non-linear shape.

Verdicts: `SIGNAL` (|r|≥0.05, p≤0.01, stable) · `weak` · `none` · `UNUSABLE`. Exit code 2 when nothing shows signal.
This is a screen, not a model: use it to decide whether a model is worth building and which features matter.

## Step B: when there's no signal, diagnose before you conclude

A null result is only a finding once you've ruled out a broken experiment.

```bash
schemakit diagnose --sql query.sql --date-col anchor_ts --value-col events_30d --cat-col segment \
   --where "segment = 'enterprise'" --key customer_id --expect-start 2024-01-01 --expect-end 2026-06-30
```

| check | what it reveals |
|---|---|
| **Date range vs expected** | data starts late / stops early / future dates / epoch & `9999-12-31` sentinels |
| **Monthly volume & zero months** | outages, partial loads, backfill gaps (the demo has a missing August) |
| **Percentiles** (p0…p100) | constant columns (p1==p99), >50% mass on one value (p25==p75), outliers (p99 ≫ p95), unexpected negatives |
| **Nulls and zeros** | default-filled columns that look like measurements |
| **Predicate impact** (`--where`) | the filter removes everything or nearly everything: typos, case, wrong enum values, NULL semantics |
| **Categorical hygiene** (`--cat-col`) | `test`/`N/A`/`unknown` placeholders; `Open` vs `open ` variants that silently miss equality filters |
| **Trend break** | a metric's definition or pipeline changed mid-series |
| **Duplicates** (`--key`) | over-weighted entities inflating or masking effects |

## Step C: statistical validation (by hand, guided)

If diagnostics are clean and signal is still absent, check it isn't a power or aggregation problem:

- **Power:** how many rows in the smaller outcome class? A rare outcome with 40 positives can't show a subtle effect.
- **Range restriction:** did your filters remove the variation (only one plan tier, one month)?
- **Wrong window:** try other lookbacks (7/30/90 days). Signal often lives at one horizon only.
- **Segment mixing:** opposite effects in two segments cancel in aggregate; split and re-run.
- **Cross-validation:** time-based split (train early, test late). A feature that works in one half and not the other is not signal.
- **Negative control:** a feature that *must not* matter (random ID hash) should come back `none`. If it doesn't, your pipeline leaks.

## Write back

Whatever you learn goes into SCHEMA.md: the outage month, the placeholder value, the safe window, the real time
column. Your *next* query starts from a better baseline.
