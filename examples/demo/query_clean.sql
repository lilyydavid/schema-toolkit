-- Churn within 60 days after the anchor, for customers active at the anchor.
-- Spine: one row per customer. Features pre-aggregated BEFORE joining (no fan-out)
-- and filtered to event_ts <= anchor (no leakage).
WITH params AS (
  SELECT '2025-12-31 23:59:59' AS anchor_ts, '2026-03-01 23:59:59' AS horizon_ts
),
spine AS (
  SELECT s.customer_id, p.anchor_ts,
         CASE WHEN s.ended_at IS NOT NULL AND s.ended_at <= p.horizon_ts THEN 1 ELSE 0 END AS churned_60d
  FROM silver_subscriptions s
  JOIN silver_customers c ON c.customer_id = s.customer_id AND c.is_test = 0
  CROSS JOIN params p
  WHERE s.started_at <= p.anchor_ts
    AND (s.ended_at IS NULL OR s.ended_at > p.anchor_ts)
),
ev AS (
  SELECT e.customer_id,
         COUNT(*)        AS events_30d,
         MAX(e.event_ts) AS last_event_ts
  FROM silver_events e, params p
  WHERE e.event_ts <= p.anchor_ts AND e.event_ts > datetime(p.anchor_ts, '-30 days')
  GROUP BY e.customer_id
),
tk AS (
  SELECT t.customer_id, COUNT(*) AS tickets_90d, MAX(t.opened_at) AS last_ticket_ts
  FROM silver_tickets t, params p
  WHERE t.opened_at <= p.anchor_ts AND t.opened_at > datetime(p.anchor_ts, '-90 days')
  GROUP BY t.customer_id
)
SELECT sp.customer_id, sp.anchor_ts, sp.churned_60d,
       COALESCE(ev.events_30d, 0)  AS events_30d,
       COALESCE(tk.tickets_90d, 0) AS tickets_90d,
       ev.last_event_ts, tk.last_ticket_ts
FROM spine sp
LEFT JOIN ev ON ev.customer_id = sp.customer_id
LEFT JOIN tk ON tk.customer_id = sp.customer_id
