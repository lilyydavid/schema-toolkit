"""Lint SCHEMA.md: is it trustworthy enough to ground an AI query?"""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict

from . import schema_md as sm

STALE_DAYS = 90


def lint(doc: str) -> list[tuple[str, str, str]]:
    """Return findings as (level, subject, message). Levels: ERROR, WARN, INFO."""
    tables = sm.parse_tables(doc)
    rels = sm.parse_relationships(doc)
    out: list[tuple[str, str, str]] = []
    if not tables:
        return [("ERROR", "SCHEMA.md", "no profiled tables found; run `schemakit profile`")]

    linked = set()
    for r in rels:
        linked.add(r["child"].rsplit(".", 1)[0])
        linked.add(r["parent"].rsplit(".", 1)[0])
        for side in ("child", "parent"):
            tname = r[side].rsplit(".", 1)[0]
            if tname not in tables:
                out.append(("WARN", r[side], f"relationship references a table that is not profiled: {tname}"))
        o = sm.pct(r["orphan"])
        subj = f"{r['child']} -> {r['parent']}"
        if "NOT unique" in r["cardinality"]:
            out.append(("ERROR", subj, "parent key is not unique; any join will duplicate rows"))
        if o is not None and o > 5:
            out.append(("WARN", subj, f"{o:.1f}% orphan rows; decide LEFT vs INNER join and document why"))

    today = dt.date.today()
    for name, t in tables.items():
        f = t["fields"]
        grain = f.get("grain", "")
        if not grain or grain.startswith("UNVERIFIED"):
            out.append(("ERROR", name, "grain is unverified"))
        elif "VIOLATED" in grain:
            out.append(("ERROR", name, "stated grain is violated by the data (duplicates present)"))
        if f.get("primary key", "NONE").startswith("NONE"):
            out.append(("WARN", name, "no primary key"))
        if f.get("time columns", "NONE").startswith("NONE"):
            out.append(("WARN", name, "no time column: cannot be windowed or leakage-checked"))
        if f.get("domain", "unclassified") in ("unclassified", ""):
            out.append(("WARN", name, "domain not set"))
        if f.get("layer", "unknown") in ("unknown", ""):
            out.append(("INFO", name, "layer not set"))
        if name not in linked and len(tables) > 1:
            out.append(("WARN", name, "no verified relationship to any other table"))
        m = re.search(r"\d{4}-\d{2}-\d{2}", f.get("profiled", ""))
        if m and (today - dt.date.fromisoformat(m.group())).days > STALE_DAYS:
            out.append(("WARN", name, f"profile older than {STALE_DAYS} days; re-run `schemakit profile`"))

    # Conflicts: same column name with different types, and twin tables across layers.
    by_col: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for name, t in tables.items():
        for c in t["columns"]:
            by_col[c["name"].lower()][c["type"].upper().split("(")[0]].append(name)
    for col, types in by_col.items():
        if len(types) > 1 and col.endswith(("id", "_at", "_date", "key")):
            desc = "; ".join(f"{ty} in {', '.join(ts)}" for ty, ts in types.items())
            out.append(("WARN", col, f"same column, different types ({desc}); casts needed in joins"))
    bare: dict[str, list[str]] = defaultdict(list)
    layer_prefix = re.compile(r"^(raw|bronze|stg|staging|silver|gold|int|dim|fct|fact|mart)_")
    for name in tables:
        bare[layer_prefix.sub("", name.rsplit(".", 1)[-1].lower())].append(name)
    for base, names in bare.items():
        if len(names) > 1:
            out.append(("INFO", base, f"same table name in multiple places ({', '.join(names)}); record which is canonical"))
    return out


def render(findings: list[tuple[str, str, str]]) -> str:
    if not findings:
        return "SCHEMA.md lint: clean."
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    lines = [f"{lv:5}  {subj}: {msg}" for lv, subj, msg in sorted(findings, key=lambda x: order[x[0]])]
    errs = sum(1 for f in findings if f[0] == "ERROR")
    return "\n".join(lines) + f"\n\n{errs} error(s), {len(findings) - errs} other finding(s)."
