# schemakit: build a `SCHEMA.md` your team and your AI can trust

You just joined a company. Thousands of tables, three layers, two tables called `customers`, and an AI assistant that
will happily write a confident, wrong join. **schemakit is the process (and the small CLI) for turning that mess into a
verified `SCHEMA.md`, then using it to write queries that are grounded, checked, and honest about when there's no signal.**

```
 architecture → domains → profile tables → validate relationships → SCHEMA.md
                                                                       │
        question → plan (params, windows, joins) → SQL → QA → signal ← ┘ → diagnostics if null
```

## The eight steps

| # | step | you do | tool | guide |
|---|---|---|---|---|
| 1 | Find the architecture: CDP, medallion layers, semantic layer | ask + look | `schemakit inventory` | [docs/01](docs/01-discover-architecture.md) |
| 2 | Name the 5–6 domains that define the business | think | `DOMAINS.md` worksheet | [docs/02](docs/02-pick-domains.md) |
| 3 | Profile each table: grain, primary key, time columns, fields | run + read | `schemakit profile` | [docs/03](docs/03-profile-tables.md) |
| 4 | Prove relationships: cardinality, match %, orphans | run + decide | `schemakit relate` | [docs/04](docs/04-validate-relationships.md) |
| 5 | Grow `SCHEMA.md` incrementally; catch conflicts | write notes | `schemakit lint` | [docs/05](docs/05-build-schema-md.md) |
| 6 | **Plan before SQL**: problem, business & data params, per-table time windows, joins | plan | `QUERY_PLAN` template + [prompts](prompts/) | [docs/06](docs/06-grounded-querying.md) |
| 7 | **QA assertions**: grain, fan-out, leakage, nulls | run | `schemakit qa` | [docs/07](docs/07-qa-and-leakage.md) |
| 8 | **Signal?** If none, diagnose: date ranges, percentiles, nulls, stray predicates, trend breaks | run | `schemakit signal` / `diagnose` | [docs/08](docs/08-signal-and-diagnostics.md) |

No Python? Every measurement has a copy-paste SQL equivalent in [`sql/`](sql/).

## Quickstart

```bash
pip install -e .                       # add a driver for your warehouse, e.g. pip install "schemakit[snowflake]"
export SCHEMAKIT_URL="snowflake://user:pass@acct/db/schema?warehouse=wh"   # any SQLAlchemy URL (read-only role!)

schemakit init                         # creates SCHEMA.md and DOMAINS.md from templates
schemakit inventory --schema silver,gold --counts --out inventory.md
schemakit profile  --table silver.customers --domain customer --layer silver --write
schemakit profile  --table silver.orders --grain order_id --write
schemakit relate   --child silver.orders.customer_id --parent silver.customers.customer_id --write
schemakit lint
```

Then give `AGENTS.md` + `SCHEMA.md` to your AI assistant and use the [prompts](prompts/) for planning, SQL, QA and diagnostics.

## Try it in 30 seconds (no warehouse needed)

```bash
bash examples/demo/run_demo.sh
```

Builds a toy SaaS warehouse (SQLite) with planted traps, then runs the whole workflow. Read the results in
[`examples/demo/output/`](examples/demo/output/), starting with
[`SCHEMA.example.md`](examples/demo/output/SCHEMA.example.md).

What it catches:

| planted trap | caught by |
|---|---|
| 3% of `events.customer_id` match no customer | `relate`: `match 97.02%, orphans 4,148` |
| `invoice_id` duplicated (1% of rows) | `profile`: `VIOLATED (346 duplicate rows)`, `lint` ERROR |
| `customer_id` INTEGER in one table, TEXT in another | `lint`: same column, different types |
| `silver_customers` vs `gold_customers` twins | `lint`: record which is canonical |
| no events at all in August 2025 | `diagnose`: `months with ZERO rows: 2025-08` |
| `Open` / `open` / `OPEN ` statuses | `diagnose`: case/whitespace variants |
| mistyped predicate removes every row | `diagnose --where`: `removes every row` |
| naive query fans out and peeks past the anchor | `qa`: `grain_unique FAIL`, `no_leakage FAIL` |
| a real effect hidden in the data | `signal`: `events_30d` r = −0.49, monotonic quintile lift |

## What `SCHEMA.md` looks like

One block per table, machine-measured, with space for your notes:

```markdown
### `silver_invoices`
- **Layer:** silver  · **Domain:** billing
- **Grain:** one row per `invoice_id` — VIOLATED (346 duplicate rows) on 2026-10-18
- **Time columns:** `invoiced_at` (…); `loaded_at` (…)
| column | type | null % | distinct | note |
**Human notes**
- **Time semantics:** loaded_at lags invoiced_at by 2 days; use invoiced_at for windows
```

plus a relationships table (cardinality · match % · orphan % · date verified), canonical join paths, per-table time
windows, and a conflicts table. Template: [`schemakit/templates/SCHEMA.template.md`](schemakit/templates/SCHEMA.template.md).

## Commands

| command | purpose | exit code |
|---|---|---|
| `init` | scaffold `SCHEMA.md`, `DOMAINS.md` | 0 |
| `inventory` | tables, guessed layer/domain, shared key columns | 0 |
| `profile` | grain / PK / nulls / time ranges → upsert into SCHEMA.md | 0 |
| `relate` | child→parent cardinality, match %, orphans → SCHEMA.md | 0 |
| `lint` | unverified grain, orphans, stale profiles, type & twin conflicts | 1 on errors |
| `qa` | grain uniqueness, population, leakage, null rates on your query | 1 on any fail |
| `signal` | feature↔label screen: permutation p, time stability, quintile lift | 2 if no signal |
| `diagnose` | coverage, gaps, percentiles, nulls, predicates, trends, dupes | 1 if red flags |

Works with anything SQLAlchemy can reach: Snowflake, BigQuery, Redshift, Postgres, Databricks, DuckDB, MySQL, SQLite.
Month bucketing is dialect-aware; if a check errors on an exotic dialect, the plain SQL in [`sql/`](sql/) is the fallback.

## Safety

- **Use a read-only role.** schemakit only issues `SELECT`s, but you should enforce that at the database.
- **Profiling scans tables.** On big tables prefer a sample or a partition-limited view; `inventory --counts` is opt-in for that reason.
- **Your `SCHEMA.md` describes your employer's data.** It's git-ignored here on purpose; don't publish it.
- `signal` is a screening tool (univariate), not a causal claim or a substitute for a model and a holdout.

## Layout

```
README.md  AGENTS.md  pyproject.toml
docs/        the method, one page per step (+ substack-post.md)
prompts/     copy-paste AI prompts for each stage
templates/   QUERY_PLAN template      schemakit/templates/  SCHEMA + DOMAINS templates
sql/         plain-SQL versions of every check
schemakit/   the CLI
examples/    demo warehouse, worked QUERY_PLAN, generated output
tests/       python -m unittest discover -s tests
```

## Contributing / license

Dialect fixes, new diagnostics and war stories welcome. MIT licensed.
