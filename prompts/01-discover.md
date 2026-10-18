# Prompt 01: discover architecture and domains

```
I just joined <company>, which <one sentence on what it sells and how it makes money>.
I have not seen the warehouse yet.

1. Propose the 5–6 business domains I should map first, each with its core entity and likely unique id.
2. List the questions I should ask the data team to find out: whether a CDP/identity layer exists, the layering
   (raw/bronze/silver/gold/semantic), the canonical customer id, how freshness is monitored, and who owns each domain.
3. Give me a checklist of `schemakit inventory` follow-ups: what to look for in its output (shared id columns,
   layer prefixes, tables with no time column, twin tables).

Do not guess table names. Output only questions and criteria; I will paste inventory output next.
```

After running `schemakit inventory`, paste `inventory.md` and ask:

```
Here is the inventory. For each domain, propose the anchor table (the table whose grain is the entity) and the
order I should profile child tables. Flag any twin or duplicate-looking tables I must reconcile. Cite the rows you used.
```
