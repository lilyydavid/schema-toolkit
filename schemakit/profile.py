"""Step 3: profile one table into a SCHEMA.md block (grain, PK, nulls, time ranges)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import inspect

from .db import quote, scalar, split_name, query
from .inventory import guess_domain, guess_layer, is_time


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def profile_table(engine, table: str, grain: list[str] | None = None, layer: str | None = None,
                  domain: str | None = None, prior: dict | None = None) -> tuple[str, dict]:
    """Return (markdown body for the machine region, facts dict)."""
    schema, t = split_name(table)
    cols = [{"name": c["name"], "type": str(c["type"])} for c in inspect(engine).get_columns(t, schema=schema)]
    if not cols:
        raise SystemExit(f"No columns found for {table}. Check the name/permissions.")
    qt = quote(engine, table)
    qc = lambda c: engine.dialect.identifier_preparer.quote(c)  # noqa: E731
    n = scalar(engine, f"SELECT COUNT(*) FROM {qt}")

    stats: dict[str, dict] = {}
    for chunk in _chunks(cols, 25):
        exprs = []
        for i, c in enumerate(chunk):
            exprs.append(f"COUNT({qc(c['name'])}) AS nn_{i}")
            exprs.append(f"COUNT(DISTINCT {qc(c['name'])}) AS d_{i}")
            if is_time(c):
                exprs.append(f"MIN({qc(c['name'])}) AS mn_{i}")
                exprs.append(f"MAX({qc(c['name'])}) AS mx_{i}")
        row = query(engine, f"SELECT {', '.join(exprs)} FROM {qt}")[0]
        for i, c in enumerate(chunk):
            stats[c["name"]] = {
                "nulls": n - row[f"nn_{i}"],
                "distinct": row[f"d_{i}"],
                "min": row.get(f"mn_{i}"),
                "max": row.get(f"mx_{i}"),
            }

    pk_cands = [c["name"] for c in cols if n and stats[c["name"]]["nulls"] == 0 and stats[c["name"]]["distinct"] == n]
    today = dt.date.today().isoformat()

    grain_cols, grain_status = None, "UNVERIFIED"
    if grain:
        missing = [g for g in grain if g not in stats]
        if missing:
            raise SystemExit(f"Grain columns not in {table}: {missing}")
        distinct_combos = scalar(
            engine, f"SELECT COUNT(*) FROM (SELECT DISTINCT {', '.join(qc(g) for g in grain)} FROM {qt}) g"
        )
        grain_cols = grain
        grain_status = "verified" if distinct_combos == n else f"VIOLATED ({n - distinct_combos:,} duplicate rows)"
    elif len(pk_cands) >= 1:
        grain_cols, grain_status = [pk_cands[0]], "inferred (unique, no nulls)"

    time_cols = [c["name"] for c in cols if is_time(c) and stats[c["name"]]["max"] is not None]
    prior = prior or {}
    layer = layer or prior.get("layer") or guess_layer(table)
    domain = domain or prior.get("domain") or guess_domain(table, [c["name"] for c in cols])

    L = [f"- **Layer:** {layer}", f"- **Domain:** {domain}"]
    if grain_cols:
        g = ", ".join(f"`{x}`" for x in grain_cols)
        L.append(f"- **Grain:** one row per {g} — {grain_status} on {today}")
        L.append(f"- **Primary key:** {g}" if not grain_status.startswith("VIOLATED") else "- **Primary key:** NONE (grain violated)")
    else:
        L.append("- **Grain:** UNVERIFIED — no single column is unique; pass `--grain a,b` to test a composite")
        L.append("- **Primary key:** NONE found")
    L.append(f"- **Row count:** {n:,}")
    if time_cols:
        rng = "; ".join(f"`{c}` ({str(stats[c]['min'])[:19]} → {str(stats[c]['max'])[:19]})" for c in time_cols)
        L.append(f"- **Time columns:** {rng}")
    else:
        L.append("- **Time columns:** NONE detected — you cannot window this table without one")
    L.append(f"- **Profiled:** {today}")
    L += ["", "| column | type | null % | distinct | note |", "|---|---|---|---|---|"]
    for c in cols:
        s = stats[c["name"]]
        null_pct = 100 * s["nulls"] / n if n else 0
        note = []
        if c["name"] in (grain_cols or []):
            note.append("grain")
        if c["name"] in pk_cands:
            note.append("unique")
        if is_time(c):
            note.append("time")
        if null_pct > 20:
            note.append("mostly null?" if null_pct > 80 else "sparse")
        if n and s["distinct"] == 1:
            note.append("constant")
        L.append(f"| `{c['name']}` | {c['type']} | {null_pct:.1f} | {s['distinct']:,} | {', '.join(note)} |")
    return "\n".join(L), {"rows": n, "grain_status": grain_status}
