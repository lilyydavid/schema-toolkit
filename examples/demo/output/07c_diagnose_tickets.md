# Diagnostics

Total rows: 19,331

## Date coverage
- `opened_at` range: 2024-01-07 09:00:00 → 2025-12-31 16:00:00  (non-null: 19,331)

| month | rows | 
|---|---|
| 2024-01 ⚠ | 37 |
| 2024-02 ⚠ | 88 |
| 2024-03 | 184 |
| 2024-04 | 241 |
| 2024-05 | 340 |
| 2024-06 | 393 |
| 2024-07 | 442 |
| 2024-08 | 560 |
| 2024-09 | 575 |
| 2024-10 | 665 |
| 2024-11 | 778 |
| 2024-12 | 825 |
| 2025-01 | 885 |
| 2025-02 | 812 |
| 2025-03 | 1,022 |
| 2025-04 | 1,068 |
| 2025-05 | 1,161 |
| 2025-06 | 1,237 |
| 2025-07 | 1,311 |
| 2025-08 | 1,366 |
| 2025-09 | 1,291 |
| 2025-10 | 1,416 |
| 2025-11 | 1,333 |
| 2025-12 | 1,301 |

## Values of `status` (5 distinct)
- `open`: 3,941 (20.4%)
- `Open`: 3,913 (20.2%)
- `OPEN `: 3,851 (19.9%)
- `Closed`: 3,835 (19.8%)
- `closed`: 3,791 (19.6%)

## Duplicates on (ticket_id): 0

## Red flags
- data ends 2025-12-31, earlier than the expected 2026-06-01; stale or partial load
- months with <20% of median volume (partial load or outage?): 2024-01, 2024-02
- status has case/whitespace variants of the same value: [['open', 'Open', 'OPEN '], ['Closed', 'closed']]; equality predicates will silently miss rows
