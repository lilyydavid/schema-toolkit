"""Step 1: map the warehouse. Lists tables, guesses layer + domain, and surfaces shared key columns."""
from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import inspect

from .db import quote, scalar

LAYERS = [
    ("raw", r"(^|[._])(raw|landing|src|source)([._]|$)"),
    ("bronze", r"(^|[._])bronze([._]|$)"),
    ("staging", r"(^|[._])(stg|staging)([._]|$)"),
    ("silver", r"(^|[._])(silver|int|intermediate|clean)([._]|$)"),
    ("gold", r"(^|[._])(gold|mart|marts|reporting|analytics)([._]|$)"),
    ("semantic", r"(^|[._])(semantic|metrics|cdp|profile)([._]|$)"),
]
DIM_FACT = [("dimension", r"(^|_)dim(_|$)"), ("fact", r"(^|_)fct?(_|$)|(^|_)fact(_|$)")]

DOMAIN_HINTS = {
    "customer": ["customer", "user", "account", "member", "contact", "profile", "person"],
    "orders": ["order", "cart", "checkout", "transaction", "purchase", "booking"],
    "billing": ["invoice", "payment", "charge", "subscription", "refund", "plan", "revenue"],
    "product": ["product", "item", "sku", "catalog", "inventory", "feature"],
    "behavior": ["event", "session", "pageview", "click", "visit", "activity", "log"],
    "support": ["ticket", "case", "support", "nps", "survey", "complaint"],
    "marketing": ["campaign", "email", "ad_", "channel", "attribution", "utm", "lead"],
}

TIME_TYPES = ("DATE", "TIME", "TIMESTAMP", "DATETIME")
TIME_NAME = re.compile(r"(_at|_date|_ts|_time|_dt|^date|^timestamp|^created|^updated)$|^(date|ts|dt)_", re.I)


def guess_layer(name: str) -> str:
    low = name.lower()
    for layer, pat in LAYERS:
        if re.search(pat, low):
            return layer
    for _kind, pat in DIM_FACT:
        if re.search(pat, low):
            return "gold"
    return "unknown"


def guess_domain(name: str, columns: list[str]) -> str:
    hay = name.lower()
    for domain, words in DOMAIN_HINTS.items():
        if any(w in hay for w in words):
            return domain
    return "unclassified"


def is_time(col: dict) -> bool:
    return str(col["type"]).upper().startswith(TIME_TYPES) or bool(TIME_NAME.search(col["name"]))


def run(engine, schemas: list[str | None], counts: bool = False) -> str:
    insp = inspect(engine)
    rows = []
    col_index: dict[str, list[str]] = defaultdict(list)
    for schema in schemas:
        for t in insp.get_table_names(schema=schema) + insp.get_view_names(schema=schema):
            full = f"{schema}.{t}" if schema else t
            cols = insp.get_columns(t, schema=schema)
            pk = insp.get_pk_constraint(t, schema=schema).get("constrained_columns") or []
            cols = [{"name": c["name"], "type": str(c["type"])} for c in cols]
            n = None
            if counts:
                try:
                    n = scalar(engine, f"SELECT COUNT(*) FROM {quote(engine, full)}")
                except Exception:  # permissions, views that fail, etc.
                    n = None
            for c in cols:
                col_index[c["name"].lower()].append(full)
            rows.append(
                {
                    "table": full,
                    "layer": guess_layer(full),
                    "domain": guess_domain(full, [c["name"] for c in cols]),
                    "ncols": len(cols),
                    "rows": n,
                    "declared_pk": ", ".join(pk) or "—",
                    "id_cols": ", ".join(c["name"] for c in cols if c["name"].lower().endswith("id"))[:60] or "—",
                    "time_cols": ", ".join(c["name"] for c in cols if is_time(c))[:60] or "—",
                }
            )
    rows.sort(key=lambda r: (r["domain"], r["layer"], r["table"]))

    out = ["# Warehouse inventory", "", "_Guesses are heuristics. Confirm the layer and domain before you trust them._", ""]
    out += [
        "| table | layer? | domain? | cols | rows | declared PK | id-like cols | time-like cols |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        nrows = "" if r["rows"] is None else format(r["rows"], ",")
        out.append(
            f"| `{r['table']}` | {r['layer']} | {r['domain']} | {r['ncols']} | "
            f"{nrows} | {r['declared_pk']} | {r['id_cols']} | {r['time_cols']} |"
        )
    shared = {c: t for c, t in col_index.items() if len(t) > 1 and (c.endswith("id") or c.endswith("key"))}
    out += ["", "## Candidate join keys (id/key columns that appear in 2+ tables)", ""]
    if shared:
        out += ["| column | appears in |", "|---|---|"]
        for c, ts in sorted(shared.items(), key=lambda kv: -len(kv[1])):
            out.append(f"| `{c}` | {', '.join(f'`{x}`' for x in ts)} |")
    else:
        out.append("_None found. Keys may be named differently per table; check by hand._")
    out += [
        "",
        "## Next",
        "",
        "1. Pick the 5–6 domains that define your business (see the domains guide, `docs/02-pick-domains.md` in the schema-toolkit repo).",
        "2. `schemakit profile --table <t> --domain <d> --layer <l> --write` for each anchor table.",
    ]
    return "\n".join(out) + "\n"
