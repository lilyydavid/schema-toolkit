# schema-toolkit: build your own `SCHEMA.md` when you join a new company

For anyone starting a data, analytics, ML or engineering job, or inheriting a data stack they didn't build. In about a
week you'll have a verified, local `SCHEMA.md`: each table's grain, keys, time columns and traps, and each join's
cardinality and orphan rate. Your AI assistant then plans queries from it instead of guessing.

- **Any company, any database.** Nothing here is specific to one industry or stack.
- **The AI never touches your database.** You run the measurements and paste the output.
- **A starting point to fork.** Delete what you don't need and add the checks your data keeps needing.

## Install: paste this into Claude Code

> Install the toolkit at https://github.com/lilydavida/schema-toolkit by following its `## Setup instructions for Claude Code` section in the README. Then run the demo, and help me build my SCHEMA.md.

## Setup instructions for Claude Code

1. Clone: `git clone https://github.com/lilydavida/schema-toolkit.git ~/schema-toolkit` (skip if it exists).
2. Install the CLI: `pip install -e ~/schema-toolkit`. Its only dependency is SQLAlchemy.
3. Install the slash commands globally: `mkdir -p ~/.claude/commands && cp ~/schema-toolkit/.claude/commands/*.md ~/.claude/commands/`
4. Run the demo: `bash ~/schema-toolkit/examples/demo/run_demo.sh`. Show the user `examples/demo/output/SCHEMA.example.md`
   and the QA output (`05a_qa_leaky.txt` vs `05b_qa_clean.txt`).
5. Tell the user the toolkit is installed. That's it. Type `/schema-init` in the folder where their `SCHEMA.md` will live.
6. Start the interview now. Ask 2–3 short questions together: what the company sells, which data stack, and the questions
   the business keeps asking. Then propose 5–6 domains and the first tables to profile, following `/schema-init`.
7. Never ask for database credentials or connect to the database yourself. Propose commands; the user runs them and
   pastes the output. Only run `schemakit` against a database if the user explicitly allows it, with a read-only role.

## Commands

| command | what it does |
|---|---|
| `/schema-init` | interview, propose domains, scaffold `SCHEMA.md` |
| `/schema-add <table>` | profile a table, prove its relationships, lint |
| `/schema-ask <question>` | plan, SQL, QA, signal check, diagnostics if there's no signal |

The method is in [`docs/`](docs/), one page per step. Every command and its manual usage is in
[`docs/reference.md`](docs/reference.md). Prefer no AI? Every check also has a plain SQL version in [`sql/`](sql/).

## Try the demo (no database needed)

```bash
bash examples/demo/run_demo.sh
```

It builds a toy SaaS data stack with planted traps and shows each one being caught, in
[`examples/demo/output/`](examples/demo/output/). Traps include orphaned keys, duplicated rows, a missing month, and a
sloppy query that fans out and leaks future data.

## Safety

- **Read-only roles only** for anything that connects. The CLI only issues `SELECT`s.
- **`--where` and `--sql` run SQL as-is.** Only use them on your own queries.
- **Your `SCHEMA.md` describes your employer's data.** It's git-ignored here; don't publish it.

## Why this exists

My real onboarding at Sephora didn't come from a training deck. About seven years ago it happened over informal
lunch-time BigQuery workshops, and that's how I built my first mental map of our tables.

Today Sephora's stack has a solid Customer Data Platform, and I've moved that mental map into a structured local file,
`bq_schema_ref.md`. It grounds my AI assistant without giving it database access, which is how I work through questions
like loyalty tier downgrades and CLV drivers. This repo generalises that process so anyone can build their own file in a
week instead of seven years. Call yours whatever you like; the default here is `SCHEMA.md`.

## License

MIT
