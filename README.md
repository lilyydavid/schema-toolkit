# schema-toolkit: build your own `SCHEMA.md` when you join a new company

I learned my last warehouse the slow way, from lunch-time workshops and a mental map in my head. This is the process I
use now, written down so anyone joining a new company can do it in a week.

**For anyone starting a new data, analytics, ML or engineering job** (or inheriting a warehouse they didn't build) who
wants to learn the tables fast and get an AI assistant that doesn't guess.

You'll end up with a verified, local `SCHEMA.md`: for each table, its grain, primary key, time columns and traps; for
each join, its cardinality and orphan rate; plus the rules for turning a business question into a query that is planned,
checked for leakage and honest about whether there's any signal.

- **Works for any company and any warehouse.** Nothing here is specific to one industry or stack.
- **A week, not years.** Pick 5–6 domains, profile their anchor tables, prove the joins, grow from there.
- **The AI never touches your database.** You run the measurements; the AI reasons from what you paste.
- **A starting point to fork.** Delete what you don't need and add the checks your data keeps needing.

## Install: paste this into Claude Code

> Install the toolkit at https://github.com/lilydavida/schema-toolkit by following its `## Setup instructions for Claude Code` section in the README. Then run the demo, and help me build my SCHEMA.md.

## Setup instructions for Claude Code

If you're Claude Code following the prompt above, do these steps in order:

1. **Clone** (skip if it exists): `git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit`
2. **Install the CLI:** `pip install -e ~/schema-toolkit` (try `pip3` / `python3 -m pip` if needed). This installs one dependency, SQLAlchemy.
3. **Install the slash commands:** `mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/`
   This is a global change: it adds `/schema-init`, `/schema-add` and `/schema-ask` to every project for this user.
4. **Run the demo** so the user sees it work with no warehouse: `bash ~/schema-toolkit/examples/demo/run_demo.sh`.
   Then show them `examples/demo/output/SCHEMA.example.md` and the QA output for the sloppy vs the grounded query
   (`05a_qa_leaky.txt`, `05b_qa_clean.txt`).
5. **Tell the user:** the toolkit is installed and the three commands are available. That's it. Type `/schema-init` in the
   project folder where they want their `SCHEMA.md` to live.
6. **Start the interview now.** Ask the user 2–3 short questions, all at once: what the company sells and how it makes money,
   which warehouse they use, and the 2–3 questions the business keeps asking. Then propose the 5–6 domains and the first
   tables to profile. Don't skip this; it's what turns the toolkit into their own. Follow `/schema-init` from there.
7. **Do NOT ask for database credentials, and do not connect to the user's warehouse yourself.** The default mode is
   that you propose a command, the user runs it, and they paste the output back. Only if the user explicitly says
   "you may run schemakit against my database" may you run it, with a read-only role.

## How you use it

| command | what it does |
|---|---|
| `/schema-init` | asks about your business, proposes the 5–6 domains and which tables to profile first, scaffolds `SCHEMA.md` |
| `/schema-add <table>` | profile a table, prove its relationships, write the entry, lint |
| `/schema-ask <question>` | plan → structured SQL → QA assertions → signal check → diagnostics if there's no signal |

The method runs in two halves. Steps 1–5 build the baseline once and keep it fresh. Steps 6–8 are the four blocks you run every time you ask a question: **what to measure**, **how to source it**, **does the data look right**, and **does it have signal, and if not, why**.

Each step has a short guide in [`docs/`](docs/), and the eight steps, manual commands and repo layout are in [`docs/reference.md`](docs/reference.md).

Prefer no AI at all? Every command runs by hand, and every check has a copy-paste SQL version in [`sql/`](sql/).

**Slash commands or prompts?** Use the slash commands in Claude Code. They're limited to running `schemakit` and editing files.
Use [`prompts/`](prompts/) when you're in a chat assistant without the commands installed.

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
- **`--where`, `--sql` and `qa --sql` paste SQL into queries as-is.** That's fine for a local tool you run on your own queries; never feed it untrusted input.
- **Use a read-only role** for anything that connects. schemakit only issues `SELECT`s, but enforce that at the database.
- **Profiling scans tables.** On big tables use a sample or partition-limited view; `inventory --counts` is opt-in.
- **Your `SCHEMA.md` describes your employer's data.** It's git-ignored here on purpose; don't publish it.
- `signal` is a univariate screen, not a causal claim or a substitute for a model and a holdout.

## Why this exists (the author's story)

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

This repo is that process, generalised, so anyone joining a new company can build their own file in a week instead of
seven years. (Call yours whatever you like. The default here is `SCHEMA.md`.)

## Adding your own checks

Each check is a small function in `schemakit/` plus a plain-SQL twin in `sql/`. Fork it, delete what you don't need,
and ask Claude to add the diagnostics *your* data keeps needing (a snapshot-consistency check, a currency-mix check…).

## License

MIT
