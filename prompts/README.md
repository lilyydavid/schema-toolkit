# Prompts

Copy-paste prompts for each stage. Put `AGENTS.md` (or its contents) in the system prompt, attach `SCHEMA.md`, then use:

| file | stage | when |
|---|---|---|
| [`01-discover.md`](01-discover.md) | architecture & domains | day 1, before touching tables |
| [`02-build-schema.md`](02-build-schema.md) | grow SCHEMA.md | per domain, repeat |
| [`03-plan-query.md`](03-plan-query.md) | plan before SQL | every analytical question |
| [`04-write-sql.md`](04-write-sql.md) | structured SQL | after the plan is approved |
| [`05-qa.md`](05-qa.md) | assertions & leakage review | before reading any result |
| [`06-no-signal.md`](06-no-signal.md) | diagnostics for a null result | when there's no signal |

The AI does the *reasoning and drafting*; `schemakit` does the *measuring*. Paste real tool output back into the chat
so the model reasons about facts, not guesses.
