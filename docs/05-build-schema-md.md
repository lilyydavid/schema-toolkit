# 5. Build SCHEMA.md incrementally

SCHEMA.md is a living baseline, not a one-off document. Grow it one verified table at a time.

## The loop

```
pick a table → profile → validate its edges to tables already in SCHEMA.md → add human notes → lint → repeat
```

Order matters: anchor tables first, then their children, then the long tail as questions demand it.
**Don't profile the whole data stack.** An unread table you never needed costs nothing; a wrong entry costs a lot.

## What SCHEMA.md contains

| § | section | written by |
|---|---|---|
| 1 | Business model → domains | you |
| 2 | Architecture (CDP, layers, platform) | you |
| 3 | Conventions (timezones, soft deletes, test accounts, currency) | you |
| 4 | **Tables**: layer, domain, grain, PK, time columns, column profile | `schemakit profile` (+ your notes) |
| 5 | **Relationships**: cardinality, match %, orphan %, date verified | `schemakit relate` |
| 6 | Canonical join paths | you |
| 7 | **Time windows per table**: event vs load time, lag, safe as-of rule | you |
| 8 | Conflicts & known traps | you (+ `schemakit lint` hints) |

Machine-written regions sit between `<!-- schemakit:begin <table> -->` and `<!-- schemakit:end <table> -->`.
Re-profiling replaces only that region. **Your notes outside it are never touched.**

## Per-table human notes (do these, they're the valuable part)

- **Time semantics:** is `created_at` when it happened or when it was loaded? What timezone? How late can rows arrive?
- **Safe window:** the date range you trust; partial months; backfills.
- **Gotchas:** test accounts, soft deletes, duplicates, "this column changed meaning in 2024".

## Keep it honest

```bash
schemakit lint            # exit 1 on errors: unverified/violated grain, non-unique parents
```

Lint also warns on: tables with no verified relationship, stale profiles (>90 days), same column / different type,
orphan rate >5%, tables with no usable time column.

Put `schemakit lint` in CI and re-profile on a schedule. A SCHEMA.md that's six months stale is worse than none,
because the AI will trust it.

## Privacy

SCHEMA.md describes your employer's data. **Don't publish it.** The repo's `.gitignore` ignores `/SCHEMA.md`.
If you want to share an example, redact or use the demo (`examples/demo/`).
