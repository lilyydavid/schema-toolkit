# Diagnostics

Total rows: 139,003
Rows surviving your predicate `event_type = 'purchase'`: 0 (0.0%)

Stopped: nothing left to inspect. Run again without --where, and with --cat-col on the filtered column to see its real values.

## Red flags
- your WHERE clause removes every row; a stray or mistyped predicate is the likeliest cause
