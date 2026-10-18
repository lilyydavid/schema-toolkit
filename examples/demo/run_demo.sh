#!/usr/bin/env bash
# End-to-end demo: build a toy warehouse, then walk the whole schemakit workflow.
# Outputs land in examples/demo/output/ so you can read what each step produces.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$HERE/output"
WORK="$(mktemp -d)"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export SCHEMAKIT_URL="sqlite:///$WORK/demo.db"
sk() { python3 -m schemakit "$@"; }
rm -rf "$OUT"; mkdir -p "$OUT"

python3 "$HERE/make_demo_db.py" "$WORK/demo.db" >/dev/null
cd "$WORK"

echo "== 1. init + inventory"
sk init >/dev/null
sk inventory --counts --out "$OUT/01_inventory.md"

echo "== 2. profile the anchor tables into SCHEMA.md"
for t in silver_customers silver_subscriptions silver_events silver_tickets gold_customers; do sk profile --table "$t" --write; done
# invoices: the single-column grain guess is wrong, so test it explicitly and let the violation be recorded
sk profile --table silver_invoices --grain invoice_id --write

echo "== 3. validate relationships with data"
rel() { sk relate --child "$1" --parent "$2" --write | head -1; }
rel silver_subscriptions.customer_id silver_customers.customer_id
rel silver_events.customer_id        silver_customers.customer_id
rel silver_tickets.customer_id       silver_customers.customer_id
rel silver_invoices.subscription_id  silver_subscriptions.subscription_id
rel silver_invoices.customer_id      silver_customers.customer_id
rel gold_customers.customer_id       silver_customers.customer_id

echo "== 4. lint (expected: 1 error for the duplicated invoices)"
sk lint | tee "$OUT/04_lint.txt"

BASE="SELECT COUNT(*) FROM silver_subscriptions s JOIN silver_customers c ON c.customer_id=s.customer_id AND c.is_test=0 WHERE s.started_at<='2025-12-31 23:59:59' AND (s.ended_at IS NULL OR s.ended_at>'2025-12-31 23:59:59')"
echo "== 5a. QA on the sloppy query (expected: FAIL fan-out + leakage)"
sk qa --sql "$HERE/query_leaky_fanout.sql" --key customer_id --anchor anchor_ts --feature-times last_event_ts,last_ticket_ts | tee "$OUT/05a_qa_leaky.txt"
echo "== 5b. QA on the grounded query (expected: all PASS)"
sk qa --sql "$HERE/query_clean.sql" --key customer_id --anchor anchor_ts --feature-times last_event_ts,last_ticket_ts --base-sql "$BASE" | tee "$OUT/05b_qa_clean.txt"

echo "== 6. signal"
sk signal --sql "$HERE/query_clean.sql" --label churned_60d --features events_30d,tickets_90d | tee "$OUT/06_signal.txt"

echo "== 7. diagnostics (a mistyped predicate, then the real table)"
sk diagnose --table silver_events --date-col event_ts --cat-col event_type --where "event_type = 'purchase'" > "$OUT/07a_diagnose_bad_predicate.md"
sk diagnose --table silver_events --date-col event_ts --cat-col event_type --key event_id --expect-start 2024-01-01 --expect-end 2026-06-01 > "$OUT/07b_diagnose_events.md"
sk diagnose --table silver_tickets --date-col opened_at --cat-col status --key ticket_id --expect-end 2026-06-01 > "$OUT/07c_diagnose_tickets.md"

cp SCHEMA.md "$OUT/SCHEMA.example.md"
echo; echo "Done. Read $OUT/SCHEMA.example.md to see the finished document."
