-- The query a model writes when it has NOT read SCHEMA.md. Two classic bugs on purpose:
--   1. FAN-OUT: events and tickets are joined raw, so rows multiply (events x tickets per customer).
--   2. LEAKAGE: no upper bound on event_ts, so the feature window runs past the anchor into the outcome period.
SELECT s.customer_id,
       '2025-12-31 23:59:59'  AS anchor_ts,
       CASE WHEN s.ended_at IS NOT NULL AND s.ended_at <= '2026-03-01 23:59:59' THEN 1 ELSE 0 END AS churned_60d,
       e.event_ts             AS last_event_ts,
       t.opened_at            AS last_ticket_ts
FROM silver_subscriptions s
JOIN silver_events  e ON e.customer_id = s.customer_id
JOIN silver_tickets t ON t.customer_id = s.customer_id
WHERE s.started_at <= '2025-12-31 23:59:59'
  AND (s.ended_at IS NULL OR s.ended_at > '2025-12-31 23:59:59')
