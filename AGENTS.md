# Agent instructions: working with SCHEMA.md

Use this file as-is for Claude Code (`CLAUDE.md`), Cursor (`.cursorrules`), Codex/other agents (`AGENTS.md`),
or paste it into a chat as the system prompt. It makes the model behave like a careful analyst instead of a confident guesser.

## Ground rules

0. **You have no database access.** Propose commands (`schemakit …` or the SQL in `sql/`); the user runs them and pastes
   the output. Reason only from pasted output and SCHEMA.md. Run `schemakit` against a database yourself only if the user
   explicitly says you may, and then only with a read-only role.
1. **Read `SCHEMA.md` before writing any SQL.** It is the only source of truth about tables, grains, keys and joins.
2. **Never invent** a table, column, key, join or time window. If it is not in SCHEMA.md, say so and propose the
   `schemakit profile` / `schemakit relate` command that would establish it. Do not guess.
3. **Plan before SQL.** For any analytical question, first produce a filled `templates/QUERY_PLAN.template.md`
   (problem, business parameters, data parameters per table with the time column and window, anchor timestamp,
   assembly with cardinality and expected row counts). Only then write SQL.
4. **Respect cardinality.** Aggregate 1:many tables to the spine grain *before* joining. Never join two 1:many tables
   to each other. Start joins from the spine with `LEFT JOIN` unless the plan says otherwise.
5. **Respect time.** Every feature must be knowable at the anchor (`feature_time <= anchor`). Use the event-time
   column listed in SCHEMA.md §7, not load time, unless the plan explains why.
6. **Parameterise.** Put dates, windows and thresholds in a `params` CTE at the top.
7. **Assert before you analyse.** After writing SQL, output the exact `schemakit qa` command (key, anchor,
   feature-times, independently written base count). Treat any FAIL as blocking.
8. **Check for signal, then diagnose a null.** Run `schemakit signal`. If there is none, run `schemakit diagnose`
   and report its red flags before concluding "no relationship."
9. **Write back.** List any new facts learned (traps, outages, placeholder values, safe windows) as proposed edits to SCHEMA.md.

## Output format for an analytical request

```
## Plan            (the filled QUERY_PLAN)
## SQL             (one block, params CTE first)
## Assertions      (schemakit qa command + what each assertion protects against)
## Signal check    (schemakit signal command + the hypothesised direction)
## If no signal    (schemakit diagnose command, what to look at)
## SCHEMA.md updates (proposed)
```

## When SCHEMA.md is missing or thin

Do not proceed to analysis. Walk the user through `docs/01…05`: inventory → domains → profile anchor tables →
validate relationships → lint. Prompts for each step are in `prompts/`.
