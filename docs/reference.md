# Reference

Everything the README leaves out: the eight steps, the manual commands, and the repo layout.

## The eight steps

| # | step | you do | tool | guide |
|---|---|---|---|---|
| 1 | Find the architecture: CDP, medallion layers, semantic layer | ask + look | `schemakit inventory` | [01](01-discover-architecture.md) |
| 2 | Name the 5–6 domains that define the business | think | `DOMAINS.md` worksheet | [02](02-pick-domains.md) |
| 3 | Profile each table: grain, primary key, time columns, fields | run + read | `schemakit profile` | [03](03-profile-tables.md) |
| 4 | Prove relationships: cardinality, match %, orphans | run + decide | `schemakit relate` | [04](04-validate-relationships.md) |
| 5 | Grow `SCHEMA.md` incrementally; catch conflicts | write notes | `schemakit lint` | [05](05-build-schema-md.md) |
| 6 | **What to measure / how to source it**: plan before SQL | plan | `QUERY_PLAN` + [prompts](../prompts/) | [06](06-grounded-querying.md) |
| 7 | **Does the data look right?** grain, fan-out, leakage, nulls | run | `schemakit qa` | [07](07-qa-and-leakage.md) |
| 8 | **Does it have signal? If not, why?** | run | `schemakit signal` / `diagnose` | [08](08-signal-and-diagnostics.md) |

Steps 1–5 build the baseline once and keep it fresh. Steps 6–8 are the four blocks you run every time you ask a question.

## Manual commands

```bash
pip install -e .                       # one dependency (SQLAlchemy); add a driver, e.g. pip install "schemakit[bigquery]"
export SCHEMAKIT_URL="bigquery://my-project/my_dataset"    # any SQLAlchemy URL; use a read-only role

schemakit init                         # creates SCHEMA.md and DOMAINS.md from templates
schemakit inventory --schema silver,gold --counts --out inventory.md
schemakit profile  --table silver.customers --domain customer --layer silver --write
schemakit profile  --table silver.orders --grain order_id --write
schemakit relate   --child silver.orders.customer_id --parent silver.customers.customer_id --write
schemakit lint
```

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

Works with anything SQLAlchemy can reach. **Only SQLite is tested in CI so far.** Month bucketing is dialect-aware but
untested elsewhere, so if a check errors on your data stack, the plain SQL in [`sql/`](../sql/) is the fallback (and please open an issue).

## Layout

```
README.md  AGENTS.md  pyproject.toml
.claude/commands/   /schema-init  /schema-add  /schema-ask
docs/        the method, one page per step, and this reference
prompts/     copy-paste AI prompts for chat-only use (the slash commands cover Claude Code)
templates/   QUERY_PLAN template      schemakit/templates/  SCHEMA + DOMAINS templates
sql/         plain-SQL versions of every check
schemakit/   the CLI
examples/    demo data stack, worked QUERY_PLAN, generated output
tests/       python -m unittest discover -s tests
```

## The four blocks

Every question runs through four blocks. Steps 6–8 in the table above are these.

1. **What to measure:** parameters and snapshot windows (`QUERY_PLAN`).
2. **How to source it:** data assembly, with each join's cardinality.
3. **Does the data look right?** QA assertions: grain, fan-out, leakage, nulls.
4. **Does it have signal? If not, why?** Signal screen, then diagnostics.

## What the demo catches

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

## Adding your own checks

Each check is a small function in `schemakit/` plus a plain-SQL twin in `sql/`. Fork it, delete what you don't need, and
ask Claude to add the diagnostics your data keeps needing.
