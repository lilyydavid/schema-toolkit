---
description: Start a SCHEMA.md for a new company; interview, propose domains, scaffold files
allowed-tools: [Bash(schemakit:*), Bash(python3 -m schemakit:*), Read, Write, Edit]
---

You are helping the user build a grounded SCHEMA.md for a data stack they have just met. Follow `docs/01` and `docs/02`
of the schema-toolkit repo (usually `~/schema-toolkit`).

**Mode: you do NOT have database access.** Propose each command, the user runs it, and they paste the output.
Only run `schemakit` against a database if the user explicitly says you may.

1. **Confidence check first.** Ask these short questions (all at once), then wait:
   - What does the company sell, and how does it make money?
   - Which data stack (BigQuery, Snowflake, Postgres, …) and is there a CDP / identity layer you know of?
   - What are the 2–3 questions the business keeps asking that you'll be expected to answer?
2. From the answers, propose **5–6 domains**, each with its core entity and likely unique id, and the questions that
   cross domains (those crossings are the relationships to prove first). Do not guess table names.
3. Run `schemakit init` in the current folder (creates `SCHEMA.md` and `DOMAINS.md`; safe, local only) and fill in
   DOMAINS.md from the answers.
4. Give the user the exact `schemakit inventory --schema <…> --counts --out inventory.md` command to run (or the SQL in
   `sql/01_discovery.sql` if they cannot install the CLI) and ask them to paste the result.
5. When they paste it: propose an **anchor table per domain** and the order to profile child tables, flag twin
   tables, and finish by telling them to use `/schema-add <table>` for each.
