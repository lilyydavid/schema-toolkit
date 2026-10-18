"""Step 4: prove a relationship with data before it goes in SCHEMA.md."""
from __future__ import annotations

import datetime as dt

from .db import quote, scalar


def _split(ref: str) -> tuple[str, str]:
    if "." not in ref:
        raise SystemExit(f"'{ref}' must look like schema.table.column or table.column")
    table, col = ref.rsplit(".", 1)
    return table, col


def check(engine, child_ref: str, parent_ref: str) -> dict:
    ct, cc = _split(child_ref)
    pt, pc = _split(parent_ref)
    qct, qpt = quote(engine, ct), quote(engine, pt)
    prep = engine.dialect.identifier_preparer
    qcc, qpc = prep.quote(cc), prep.quote(pc)

    child_rows = scalar(engine, f"SELECT COUNT(*) FROM {qct}")
    child_nn = scalar(engine, f"SELECT COUNT({qcc}) FROM {qct}")
    child_distinct = scalar(engine, f"SELECT COUNT(DISTINCT {qcc}) FROM {qct}")
    parent_rows = scalar(engine, f"SELECT COUNT({qpc}) FROM {qpt}")
    parent_distinct = scalar(engine, f"SELECT COUNT(DISTINCT {qpc}) FROM {qpt}")
    matched = scalar(
        engine,
        f"SELECT COUNT(*) FROM {qct} c WHERE c.{qcc} IS NOT NULL "
        f"AND EXISTS (SELECT 1 FROM {qpt} p WHERE p.{qpc} = c.{qcc})",
    )
    parent_unique = parent_rows == parent_distinct
    child_unique = child_nn == child_distinct
    if not parent_unique:
        card = "many:many (parent key NOT unique — joins fan out)"
    elif child_unique:
        card = "1:1"
    else:
        card = "many:1"
    # How many parent keys are never referenced (useful for spotting dead dimension rows).
    unreferenced = scalar(
        engine,
        f"SELECT COUNT(DISTINCT p.{qpc}) FROM {qpt} p WHERE NOT EXISTS "
        f"(SELECT 1 FROM {qct} c WHERE c.{qcc} = p.{qpc})",
    )
    return {
        "child": child_ref,
        "parent": parent_ref,
        "cardinality": card,
        "child_rows": child_rows,
        "child_null_pct": 100 * (child_rows - child_nn) / child_rows if child_rows else 0.0,
        "match_pct": 100 * matched / child_nn if child_nn else 0.0,
        "orphan_pct": 100 * (child_nn - matched) / child_nn if child_nn else 0.0,
        "orphans": child_nn - matched,
        "unreferenced_parents": unreferenced,
        "parent_unique": parent_unique,
    }


def to_row(r: dict, note: str = "") -> str:
    today = dt.date.today().isoformat()
    extra = f"{r['child_null_pct']:.1f}% null FK; {r['unreferenced_parents']:,} unreferenced parents"
    note = f"{note}; {extra}" if note else extra
    return (
        f"| `{r['child']}` | `{r['parent']}` | {r['cardinality']} | {r['match_pct']:.2f}% | "
        f"{r['orphan_pct']:.2f}% | {today} | {note} |"
    )


def render(r: dict) -> str:
    flag = "OK" if r["orphan_pct"] < 1 and r["parent_unique"] else "REVIEW"
    return (
        f"[{flag}] {r['child']} -> {r['parent']}\n"
        f"  cardinality : {r['cardinality']}\n"
        f"  match       : {r['match_pct']:.2f}%  (orphans: {r['orphans']:,}, null FK: {r['child_null_pct']:.1f}%)\n"
        f"  unreferenced parent keys: {r['unreferenced_parents']:,}"
    )
