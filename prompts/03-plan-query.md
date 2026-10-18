# Prompt 03: plan before SQL

```
Problem: <business question in plain words>.
Decision it informs: <what changes if the answer is X vs Y>.

Using ONLY SCHEMA.md (attached), produce a filled QUERY_PLAN (use the template structure):

1. Restate the problem as: unit of analysis, outcome/label definition, population, exclusions, observation window, outcome window.
2. Business parameters vs data parameters. For EACH table you intend to use: role (spine/feature/label), grain,
   key, which time column (event vs load) and the window applied to it. Windows differ per table; justify each from SCHEMA.md §7.
3. Anchor timestamp, and the leakage rule for every feature.
4. Assembly: spine, join order, cardinality of each join (from §5), which sides to pre-aggregate, join type,
   expected row count after each step.
5. List everything you needed but SCHEMA.md does not state. For each, give the schemakit command that would establish it.
   Do NOT fill the gap with a guess.

Stop after the plan. I will approve it before you write SQL.
```
