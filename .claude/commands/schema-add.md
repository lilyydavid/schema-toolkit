---
description: Add one table to SCHEMA.md; profile it, prove its relationships, lint
allowed-tools: [Bash(schemakit:*), Bash(python3 -m schemakit:*), Read, Write, Edit]
argument-hint: <schema.table>
---

Add `$ARGUMENTS` to the user's SCHEMA.md following `docs/03`, `docs/04`, `docs/05` of the schema-toolkit repo.

**Mode: you do NOT have database access.** Give the user each command; they run it and paste the output.
Only run `schemakit` against a database if they explicitly allow it.

1. Read `SCHEMA.md` so you know which tables and relationships already exist.
2. Give the user: `schemakit profile --table $ARGUMENTS --domain <d> --layer <l> --write`
   (add `--grain a,b` if the grain is likely composite). Ask them to paste what it prints.
3. From the output, say whether the grain holds. If **VIOLATED**, keep it in SCHEMA.md and list the likeliest causes and
   the query that would confirm each.
4. Identify keys that should link to tables already in SCHEMA.md. For each, give
   `schemakit relate --child … --parent … --write`, ask for the output, then decide **LEFT vs INNER** from the
   match/orphan rates and say why.
5. Draft the **Human notes** for the table: time semantics (event vs load time, timezone, lag), safe window, gotchas.
   Mark anything you are inferring rather than reading from output as UNVERIFIED.
6. Finish with `schemakit lint`; order any findings by how likely they are to cause a wrong query.

Never invent a column, key or join that is not in the pasted output or SCHEMA.md.
