# Prompt 06: no signal? diagnose before concluding

Paste the `schemakit signal` output and the `schemakit diagnose` report.

```
QA passed but `schemakit signal` found no signal for <business problem>. Diagnostics are attached.

1. Rank the red flags by how likely each is to be hiding a real effect. Cite the line in the report.
2. For each, give the query or fix to test it, and what result would confirm vs rule it out.
3. Walk this checklist and say which items the data already answers:
   date range & gaps · percentiles non-degenerate · nulls/zeros/default fills · stray or mistyped predicates
   (case, whitespace, NULL semantics) · trend breaks (definition changes) · placeholder/test values ·
   duplicates · too few positives (power) · range restriction from my filters · wrong lookback window ·
   segments with opposite effects · time-split stability · negative control.
4. If everything is clean, say so plainly and state what the null result does and does not rule out.
5. List what to write back into SCHEMA.md (outages, placeholders, real time columns, safe windows).
```
