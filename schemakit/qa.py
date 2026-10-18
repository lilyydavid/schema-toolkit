"""Step 6: QA assertions on an assembled dataset (the SQL your AI/you wrote)."""
from __future__ import annotations

from sqlalchemy import text

from .db import scalar


def run(engine, sql: str, key: list[str], anchor: str | None = None, feature_times: list[str] | None = None,
        max_null_pct: float = 50.0, base_sql: str | None = None, min_rows: int = 1) -> list[dict]:
    """Run assertions against `sql`. Each result: {check, ok, detail}."""
    src = f"({sql.strip().rstrip(';')}) AS q"
    res: list[dict] = []

    def add(check: str, ok: bool, detail: str):
        res.append({"check": check, "ok": ok, "detail": detail})

    n = scalar(engine, f"SELECT COUNT(*) FROM {src}")
    add("row_count", n >= min_rows, f"{n:,} rows (min {min_rows})")

    prep = engine.dialect.identifier_preparer
    kcols = ", ".join(prep.quote(k) for k in key)
    dups = scalar(engine, f"SELECT COUNT(*) FROM (SELECT {kcols} FROM {src} GROUP BY {kcols} HAVING COUNT(*) > 1) d")
    add("grain_unique", dups == 0, f"{dups:,} duplicated key(s) on ({', '.join(key)}); fan-out from a join if > 0")

    null_keys = scalar(
        engine, f"SELECT COUNT(*) FROM {src} WHERE " + " OR ".join(f"{prep.quote(k)} IS NULL" for k in key)
    )
    add("key_not_null", null_keys == 0, f"{null_keys:,} rows with a NULL key part")

    if base_sql:
        base = scalar(engine, base_sql.strip().rstrip(";"))
        add("population_preserved", base == n, f"base population {base:,} vs output {n:,} (diff {n - base:+,})")

    if anchor and feature_times:
        for ft in feature_times:
            bad = scalar(
                engine,
                f"SELECT COUNT(*) FROM {src} WHERE {prep.quote(ft)} IS NOT NULL AND {prep.quote(ft)} > {prep.quote(anchor)}",
            )
            add(f"no_leakage[{ft}]", bad == 0, f"{bad:,} rows where {ft} is AFTER anchor {anchor}")
    elif feature_times and not anchor:
        add("no_leakage", False, "feature time columns given but no --anchor column")

    with engine.connect() as conn:
        cols = list(conn.execute(text(f"SELECT * FROM {src} WHERE 1=0")).keys())
        if n:
            exprs = ", ".join(f"COUNT({prep.quote(c)}) AS c{i}" for i, c in enumerate(cols))
            row = conn.execute(text(f"SELECT {exprs} FROM {src}")).mappings().first()
            for i, c in enumerate(cols):
                pct = 100 * (n - row[f"c{i}"]) / n
                if pct > max_null_pct:
                    add(f"nulls[{c}]", False, f"{pct:.1f}% null (limit {max_null_pct:.0f}%)")
    return res


def render(results: list[dict]) -> str:
    lines = [f"{'PASS' if r['ok'] else 'FAIL'}  {r['check']}: {r['detail']}" for r in results]
    failed = sum(1 for r in results if not r["ok"])
    lines.append(f"\n{len(results) - failed}/{len(results)} checks passed" + ("" if not failed else " — do NOT trust this dataset yet."))
    return "\n".join(lines)
