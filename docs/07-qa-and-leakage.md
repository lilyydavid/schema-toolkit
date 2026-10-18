# 7. QA and validation assertions

Run these on the *assembled* dataset before you look at a single result. A passing dataset can still be wrong,
but a failing one is always wrong.

| assertion | catches | `schemakit qa` flag |
|---|---|---|
| **Grain unique** on the output key | join fan-out, duplicated source rows | `--key` |
| **Key not null** | broken spine, bad joins | `--key` |
| **Population preserved**: output rows = expected spine count | silent `INNER JOIN` drops, fan-out | `--base-sql` |
| **No leakage**: every feature time ≤ anchor | using the future to explain the past | `--anchor`, `--feature-times` |
| **Null rate per column** | broken join keys, windows with no data | `--max-null-pct` |
| **Row count > 0 / in expected range** | wrong filters, empty windows | `--min-rows` |

```bash
schemakit qa --sql query.sql --key customer_id \
  --anchor anchor_ts --feature-times last_event_ts,last_ticket_ts \
  --base-sql "SELECT COUNT(*) FROM ... /* the spine, written independently */"
```

Exit code 1 on any failure, so it drops into CI or a notebook cell.

## Leakage: the one that makes results *look great*

Leakage almost always shows up as a result that's too good. Typical sources:

- feature window has no upper bound (`event_ts <= anchor` missing)
- using a column that is a consequence of the outcome (`churned_at`, `refund_amount`, `final_status`)
- a mutable "current state" column used as a historical feature (the gold table's `plan_tier` *today*, not at the anchor)
- load-time vs event-time mismatch: data that wasn't *available* at the anchor even though it *happened* before it
- label windows overlapping feature windows

Rule of thumb: for each feature, ask "could a person have known this value at the anchor timestamp?"

Add a feature-time column for every feature table you join, expose it in the output, and let `--feature-times` assert it.

## Independent base count

`--base-sql` should be written **separately** from the main query (a different path to the same number). If both
share the same bug, the check proves nothing.

Plain-SQL versions: [`sql/04_qa_assertions.sql`](../sql/04_qa_assertions.sql).
