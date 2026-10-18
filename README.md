# schema-toolkit: build your own `SCHEMA.md` when you join a company

You just joined a company, or you inherited a data stack you didn't build. There are hundreds of tables, two of them
are called `customers`, and your AI assistant will happily write a join that looks right and isn't.

This toolkit fixes that. In about a week you get a `SCHEMA.md` that you have verified yourself: what each table's row
means, its keys, its time columns, its traps, and how the tables join. Then your AI plans queries from that file instead
of guessing.

It's a starting point, not a finished product. Fork it, delete what you don't need, and add the checks your data keeps needing.

## What's in it

- **`schemakit`**, a small command-line tool that measures your tables and checks your joins.
- **Three slash commands** for Claude Code: `/schema-init`, `/schema-add` and `/schema-ask`.
- **Eight short guides** in `docs/`, one per step.
- **Plain SQL** for every check in `sql/`, if you'd rather not install anything.
- **A demo** with a fake database full of planted mistakes, so you can see each one get caught.

## Install: paste this into Claude Code

> Install the toolkit at https://github.com/lilydavida/schema-toolkit by following its `## Setup instructions for Claude Code` section in the README. Then run the demo, and help me build my SCHEMA.md.

That's it. Claude will clone the repo, install the tool, add the slash commands, run the demo, and start asking you about
your company.

## Setup instructions for Claude Code

If you're Claude Code following the prompt above, do these steps in order:

1. **Clone** (skip if it exists): `git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit`
2. **Install the CLI:** `pip install -e ~/schema-toolkit`. The only dependency is SQLAlchemy.
3. **Install the slash commands** globally, so they work in every project:
   `mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/`
4. **Run the demo** so the user sees it work with no database: `bash ~/schema-toolkit/examples/demo/run_demo.sh`.
   Show them `examples/demo/output/SCHEMA.example.md` and the QA output (`05a_qa_leaky.txt` vs `05b_qa_clean.txt`).
5. **Tell the user** the toolkit is installed. Type `/schema-init` in the folder where their `SCHEMA.md` should live.
6. **Start the interview now.** Ask 2–3 short questions together: what the company sells, which database it runs on, and
   the questions the business keeps asking. Then propose 5–6 domains and the first tables to profile, following `/schema-init`.
7. **Never ask for database credentials, and don't connect to the database yourself.** Propose commands; the user runs
   them and pastes the output back. Only run `schemakit` against a database if the user explicitly allows it, using a read-only role.

## Manual install

If you'd rather do it yourself:

```bash
pip install -e ~/schema-toolkit
bash ~/schema-toolkit/examples/demo/run_demo.sh      # optional: see it work first
cd ~/my-project && schemakit init                      # creates SCHEMA.md and DOMAINS.md
```

You'll need Python 3.9 or newer. The slash commands need Claude Code; everything else works without it.

## Connect to your database (optional)

`schemakit` reads the database from `SCHEMAKIT_URL`. It takes any SQLAlchemy URL:

```bash
export SCHEMAKIT_URL="bigquery://my-project/my_dataset"
# or: export SCHEMAKIT_URL="postgresql://user:pass@host/db"
```

Install the driver for your database, for example `pip install "schemakit[bigquery]"`. Use a read-only role. Only SQLite
is tested so far. For anything else, the plain SQL in [`sql/`](sql/) is the fallback, and please open an issue if a
command fails on your database.

## Commands

| command | what it does |
|---|---|
| `/schema-init` | interview you, propose domains, create `SCHEMA.md` |
| `/schema-add <table>` | profile one table, check its joins, lint the file |
| `/schema-ask <question>` | plan the query, write the SQL, run QA, check for signal, diagnose if there's none |

The method is in [`docs/`](docs/), one page per step. Every command and its manual usage is in
[`docs/reference.md`](docs/reference.md).

## Try the demo (no database needed)

```bash
bash examples/demo/run_demo.sh
```

It builds a fake SaaS database with planted mistakes, then runs the whole workflow. Read the results in
[`examples/demo/output/`](examples/demo/output/). The mistakes include orphaned keys, duplicate rows, a missing month,
and a sloppy query that peeks at the future.

## Safety

- **Use read-only roles** for anything that connects. The CLI only runs `SELECT`s.
- **`--where` and `--sql` run SQL as-is.** Only use them on your own queries.
- **Your `SCHEMA.md` describes your employer's data.** It's git-ignored here, so don't publish it.

## Adding your own checks

1. Write a function in `schemakit/` for the check you need.
2. Add the same check as plain SQL in `sql/`, so people without the tool can run it.
3. Add a test in `tests/test_toolkit.py`, then run `python3 -m unittest discover -s tests`.

## Why this exists

My real onboarding at Sephora didn't come from a training deck. About seven years ago it happened over informal
lunch-time BigQuery workshops, and that's how I built my first mental map of our tables.

Today Sephora's stack has a solid Customer Data Platform. I've moved that mental map into a structured local file,
`bq_schema_ref.md`. It grounds my AI assistant without giving it database access, which is how I work through questions
like loyalty tier downgrades and CLV drivers.

This repo is that process, generalised. Call your file whatever you like. The default here is `SCHEMA.md`.

## License

MIT
