# schema-toolkit: build your own `SCHEMA.md` when you join a company

You just joined a company, or you inherited a data stack you didn't build. There are hundreds of tables, two of them
are called `customers`, and your AI assistant will happily write a join that looks right and isn't.

This toolkit fixes that. In about a week you get a `SCHEMA.md` that you have verified yourself: what each table's row
means, its keys, its time columns, its traps, and how the tables join. Then your AI plans queries from that file instead
of guessing.

It's a starting point, not a finished product. Fork it, delete what you don't need, and add the checks your data keeps needing.

## The idea

My real onboarding at Sephora didn't come from a training deck. About seven years ago it happened over informal
lunch-time BigQuery workshops, and that's how I built my first mental map of our tables.

Today Sephora's stack has a solid Customer Data Platform. I've moved that mental map into a structured local file,
`bq_schema_ref.md`. It grounds my AI assistant without giving it database access, which is how I work through questions
like loyalty tier downgrades and CLV drivers.

This repo is that process, generalised. Call your file whatever you like. The default here is `SCHEMA.md`.

## What's in it

- **`schemakit`**, a small command-line tool that measures your tables and checks your joins.
- **Three slash commands** for Claude Code: `/schema-init`, `/schema-add` and `/schema-ask`.
- **Eight short guides** in `docs/`, one per step.
- **Plain SQL** for every check in `sql/`, if you'd rather not install anything.
- **A demo** with a fake database full of planted mistakes, so you can see each one get caught.

## Install

Paste this into Claude Code:

> Install the toolkit at https://github.com/lilydavida/schema-toolkit by following its `INSTALL.md`. Then run the demo, and help me build my SCHEMA.md.

Or do it yourself (Python 3.9+):

```bash
git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit
pip install -e ~/schema-toolkit
mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/   # slash commands, needs Claude Code
```

Then run `schemakit init` in the folder where your `SCHEMA.md` should live.

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

## License

MIT
