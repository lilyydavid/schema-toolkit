# 3. Profile each table: grain, primary key, fields

For every table in a domain you record: **what is one row?**

## What to capture

| field | meaning | how to test it |
|---|---|---|
| **Grain** | the thing one row represents ("one row per order line") | `COUNT(*) = COUNT(DISTINCT <candidate key>)` |
| **Primary key** | the column(s) that identify a row | unique + no NULLs |
| **Time columns** | event time, load time, valid-from/to | min/max, null rate, are they timestamps or strings? |
| **Row count & freshness** | scale and last load | `COUNT(*)`, `MAX(loaded_at)` |
| **Null / distinct profile** | which columns are usable | per-column null % and distinct count |
| **Semi-structured fields** | JSON/VARIANT/STRUCT payloads | see below |

## JSON / semi-structured columns

Event and CDP tables often hide the interesting fields in a JSON column. Record, in the table's *Human notes*:

- the column name and its format (JSON string, VARIANT, STRUCT)
- the 5–10 keys you actually need and their types (`properties.plan`, `properties.amount`)
- whether keys vary by `event_type` (they usually do)
- the extraction expression for your data stack (`properties:plan::string`, `JSON_EXTRACT_SCALAR(...)`, `properties->>'plan'`)

Sample first: `SELECT <json_col> FROM t LIMIT 50` and list the union of keys. `schemakit` profiles the column like any other (null rate, distinct count); you document the keys by hand.

## Run it

```bash
schemakit profile --table silver_orders --domain orders --layer silver --write
schemakit profile --table silver_invoices --grain invoice_id,line_no --write   # composite grain
```

If the stated grain doesn't hold you get `VIOLATED (346 duplicate rows)`: **keep it**. A recorded violation is more
valuable than a hidden one. It's also the single most common cause of inflated numbers.

## Gotchas to watch for while reading the profile

- A `*_id` column that's unique but ~100% null elsewhere is a sparse optional key, not a primary key.
- Two time columns: one is event time, the other load time. Windows on the wrong one shift your numbers.
- Constant columns and mostly-null columns: drop them from consideration early.
- `SCD2` tables (valid_from / valid_to / is_current): grain is *per version*, not per entity.

Pure SQL: [`sql/02_profile.sql`](../sql/02_profile.sql).
