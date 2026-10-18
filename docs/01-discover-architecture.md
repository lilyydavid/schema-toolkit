# 1. Discover the architecture

Goal: know *where* the trustworthy data lives before you read a single column.

## What you're looking for

| question | why it matters | where to look |
|---|---|---|
| Is there a customer data platform (CDP) or identity layer? | It owns the canonical customer id. Everything joins through it. | Segment/mParticle/RudderStack config, an `identity_*` or `profile_*` schema, ask the data platform team |
| Is there a medallion (raw → silver → gold) or similar layering? | Tells you which layer has cleaned, deduplicated, business-ready grain. | Schema names: `raw`, `bronze`, `stg_`, `silver`, `int_`, `gold`, `mart`, `dim_`, `fct_` |
| Is there a semantic / metrics layer **on top**? | Its metric definitions are the company's "official" numbers. Your query should reproduce them, not invent new ones. | dbt metrics, LookML, Cube, Looker explores, BI certified datasets |
| Who loads what, and how fresh is it? | A table that stopped loading in March is a trap. | Orchestrator (Airflow/dbt Cloud), `max(loaded_at)` per table |

## The rule of thumb

**Query from the highest layer that still has the grain you need.** Gold is convenient but may have pre-aggregated away
the detail you want. Raw has everything but is messy. Silver is usually the sweet spot for analysis.

## Run it

```bash
schemakit inventory --schema silver,gold --counts --out inventory.md
```

You get every table with a guessed layer and domain, row counts, id-like and time-like columns, and a list of
**id columns that appear in 2+ tables**: your first join-key candidates.

Pure SQL instead? See [`sql/01_discovery.sql`](../sql/01_discovery.sql).

## Write down (SCHEMA.md §2 Architecture)

- the platform, the identity layer, the layers and what each means *here*
- which layer you'll query from by default
- the semantic layer's names for the metrics you'll be asked about

## Also do

- Ask for the ERD or dbt docs. Treat them as hypotheses, not facts: you'll verify with queries in step 4.
- Find the person who knows. Put their name in DOMAINS.md §5. One 20-minute chat saves a week.
