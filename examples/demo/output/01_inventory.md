# Data stack inventory

_Guesses are heuristics. Confirm the layer and domain before you trust them._

| table | layer? | domain? | cols | rows | declared PK | id-like cols | time-like cols |
|---|---|---|---|---|---|---|---|
| `silver_events` | silver | behavior | 4 | 139,003 | event_id | event_id, customer_id | event_ts |
| `silver_invoices` | silver | billing | 6 | 35,538 | — | invoice_id, subscription_id, customer_id | invoiced_at, loaded_at |
| `silver_subscriptions` | silver | billing | 5 | 2,000 | subscription_id | subscription_id, customer_id | started_at, ended_at |
| `gold_customers` | gold | customer | 4 | 2,000 | — | customer_id | updated_at |
| `silver_customers` | silver | customer | 5 | 2,000 | customer_id | customer_id | signup_at |
| `silver_tickets` | silver | support | 5 | 19,331 | ticket_id | ticket_id, customer_id | opened_at |

## Candidate join keys (id/key columns that appear in 2+ tables)

| column | appears in |
|---|---|
| `customer_id` | `gold_customers`, `silver_customers`, `silver_events`, `silver_invoices`, `silver_subscriptions`, `silver_tickets` |
| `subscription_id` | `silver_invoices`, `silver_subscriptions` |

## Next

1. Pick the 5–6 domains that define your business (see the domains guide, `docs/02-pick-domains.md` in the schema-toolkit repo).
2. `schemakit profile --table <t> --domain <d> --layer <l> --write` for each anchor table.
