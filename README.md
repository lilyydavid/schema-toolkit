# schema-toolkit: know your tables before you write your 100-day plan

A process, and a small CLI, for building a local `SCHEMA.md` that grounds your AI assistant in your warehouse: tables,
grains, keys, relationships, time windows, traps. The AI never touches your database. You run the measurements; the AI reasons from what you paste.

## The idea

My real onboarding at Sephora didn't come from a training deck.

About seven years ago, when I joined, it happened over informal lunch-time BigQuery workshops. We dove deep into data
flows, schema quirks, table relationships. That's how I built my initial mental map of our table structures. I couldn't
have started better.

Fast forward to today. Sephora's data stack now features a solid Customer Data Platform, built over time by our
Analytics Engineering function. As I step into leading Data & ML initiatives, my way of navigating that landscape has
evolved. I've moved away from a personal mental map to a structured local artifact: `bq_schema_ref.md`.

Even without giving LLMs direct database access, having this context loaded in my IDE lets me dive straight into
problem-solving. Recently I was brainstorming ways to investigate loyalty tier downgrades and validating CLV drivers.
Once the scope and constraints are defined, the schema context grounds the AI to structure queries in clear blocks:

1. **What to measure:** parameters, snapshot windows
2. **How to source it:** data assembly
3. **Does the data look right?** QA, assertions
4. **Does it have signal? If not, why?** statistical validation, diagnostics

My 2¢: know your tables before writing your 100-day plan.

This repo is that process, generalised, so someone joining a new company can build their own file in a week instead of
seven years. (Call yours whatever you like. The default here is `SCHEMA.md`.)

## Install: paste this into Claude Code

> Install the toolkit at https://github.com/lilydavida/schema-toolkit by following its `## Setup instructions for Claude Code` section in the README. Then run the demo.

## Setup instructions for Claude Code

If you're Claude Code following the prompt above, do these in order:

1. **Clone** (skip if it exists): `git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit`
2. **Install the CLI:** `pip install -e ~/schema-toolkit` (try `pip3` / `python3 -m pip` if needed).
3. **Install the slash commands:** `mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/`
   This gives the user `/schema-init`, `/schema-add` and `/schema-ask`.
4. **Run the demo** so the user sees it work with no warehouse: `bash ~/schema-toolkit/examples/demo/run_demo.sh`,
   then show them `examples/demo/output/SCHEMA.example.md` and the QA output for the sloppy vs the grounded query
   (`05a_qa_leaky.txt`, `05b_qa_clean.txt`).
5. **Tell the user:** the toolkit is installed; type `/schema-init` in the project folder where they want their `SCHEMA.md` to live.
6. **Do NOT ask for database credentials, and do not connect to the user's warehouse yourself.** The default mode is
   that you propose a command, the user runs it, and they paste the output back. Only if the user explicitly says
   "you may run schemakit against my database" may you run it, with a read-only role.

## How you use it

| command | what it does |
|---|---|
| `/schema-init` | asks about your business, proposes the 5–6 domains and which tables to profile first, scaffolds `SCHEMA.md` |
| `/schema-add <table>` | profile a table, prove its relationships, write the entry, lint |
| `/schema-ask <question>` | plan → structured SQL → QA assertions → signal check → diagnostics if there's no signal |

Prefer no AI at all? Everything is plain commands (below), and every check has a copy-paste SQL version in [`sql/`](sql/).

## The eight steps

| # | step | you do | tool | guide |
|---|---|---|---|---|
| 1 | Find the architecture: CDP, medallion layers, semantic layer | ask + look | `schemakit inventory` | [docs/01](docs/01-discover-architecture.md) |
| 2 | Name the 5–6 domains that define the business | think | `DOMAINS.md` worksheet | [docs/02](docs/02-pick-domains.md) |
| 3 | Profile each table: grain, primary key, time columns, fields | run + read | `schemakit profile` | [docs/03](docs/03-profile-tables.md) |
| 4 | Prove relationships: cardinality, match %, orphans | run + decide | `schemakit relate` | [docs/04](docs/04-validate-relationships.md) |
| 5 | Grow `SCHEMA.md` incrementally; catch conflicts | write notes | `schemakit lint` | [docs/05](docs/05-build-schema-md.md) |
| 6 | **What to measure / how to source it**: plan before SQL | plan | `QUERY_PLAN` + [prompts](prompts/) | [docs/06](docs/06-grounded-querying.md) |
| 7 | **Does the data look right?** grain, fan-out, leakage, nulls | run | `schemakit qa` | [docs/07](docs/07-qa-and-leakage.md) |
| 8 | **Does it have signal? If not, why?** | run | `schemakit signal` / `diagnose` | [docs/08](docs/08-signal-and-diagnostics.md) |

Steps 1–5 build the baseline once and keep it fresh. Steps 6–8 are your four blocks, every time you ask a question.

## Manual install and commands

```bash
pip install -e .                       # add a driver for your warehouse, e.g. pip install "schemakit[bigquery]"
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

Works with anything SQLAlchemy can reach. Only SQLite is tested in CI so far; month bucketing is dialect-aware but
untested elsewhere, so if a check errors on your warehouse, the plain SQL in [`sql/`](sql/) is the fallback (and please open an issue).

## Try it in 30 seconds (no warehouse needed)

```bash
bash examples/demo/run_demo.sh
```

Builds a toy SaaS warehouse (SQLite) with planted traps, then runs the whole workflow into
[`examples/demo/output/`](examples/demo/output/). A worked plan: [`QUERY_PLAN.example.md`](examples/demo/QUERY_PLAN.example.md).

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

## Safety

- **The AI gets no database access by default.** You run commands and paste output. `AGENTS.md` enforces this.
- **Use a read-only role** for anything that connects. schemakit only issues `SELECT`s, but enforce that at the database.
- **Profiling scans tables.** On big tables use a sample or partition-limited view; `inventory --counts` is opt-in.
- **Your `SCHEMA.md` describes your employer's data.** It's git-ignored here on purpose; don't publish it.
- `signal` is a univariate screen, not a causal claim or a substitute for a model and a holdout.

## Adding your own checks

Each check is a small function in `schemakit/` plus a plain-SQL twin in `sql/`. Fork it, delete what you don't need,
and ask Claude to add the diagnostics *your* data keeps needing (a loyalty-tier snapshot check, a currency-mix check…).

## Layout

```
README.md  AGENTS.md  pyproject.toml
.claude/commands/   /schema-init  /schema-add  /schema-ask
docs/        the method, one page per step (+ substack-post.md)
prompts/     copy-paste AI prompts for chat-only use
templates/   QUERY_PLAN template      schemakit/templates/  SCHEMA + DOMAINS templates
sql/         plain-SQL versions of every check
schemakit/   the CLI
examples/    demo warehouse, worked QUERY_PLAN, generated output
tests/       python -m unittest discover -s tests
```

## License

MIT
