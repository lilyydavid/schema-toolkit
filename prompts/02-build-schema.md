# Prompt 02: grow SCHEMA.md

Run `schemakit profile` / `schemakit relate` yourself, paste the output, then:

```
Here is the profile of <table> and the relate output for its keys (below). Using only this output and the current SCHEMA.md:

1. Is the stated grain trustworthy? If violated, what are the likeliest causes and which query would confirm each?
2. Which columns look like keys, event time, load time, status/enum, JSON payload?
3. For each relationship: LEFT or INNER join, and why, given the match/orphan rates?
4. What belongs in the "Human notes" (time semantics, safe window, gotchas) and what must I verify to fill each?
5. Name any conflict with tables already in SCHEMA.md (same concept, same column name with different type, two canonical candidates).

Propose edits to SCHEMA.md as a diff. Mark anything you are inferring rather than reading from the output as UNVERIFIED.
```

Repeat per table. Finish each session with `schemakit lint` and paste its findings:

```
Here is the lint output. Order the findings by how likely they are to produce a wrong query, and give me the one
command that would resolve each.
```
