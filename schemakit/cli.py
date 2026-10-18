"""schemakit command line."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from . import schema_md as sm


def _engine(a):
    from .db import connect

    url = a.url or os.environ.get("SCHEMAKIT_URL")
    if not url:
        raise SystemExit("No database URL. Pass --url or set SCHEMAKIT_URL (SQLAlchemy format, e.g. sqlite:///demo.db).")
    return connect(url)


def _read_sql(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text()


def cmd_init(a):
    dest = Path(a.dir)
    dest.mkdir(parents=True, exist_ok=True)
    for src, name in [("SCHEMA.template.md", "SCHEMA.md"), ("DOMAINS.template.md", "DOMAINS.md")]:
        p = dest / name
        if p.exists() and not a.force:
            print(f"skip {p} (exists; use --force to overwrite)")
            continue
        p.write_text(sm.template(src))
        print(f"wrote {p}")
    print("\nNext: fill in DOMAINS.md, then `schemakit inventory`.")


def cmd_inventory(a):
    from .inventory import run

    schemas = [s or None for s in (a.schema.split(",") if a.schema else [None])]
    md = run(_engine(a), schemas, counts=a.counts)
    if a.out:
        Path(a.out).write_text(md)
        print(f"wrote {a.out}")
    else:
        print(md)


def cmd_profile(a):
    from .profile import profile_table

    eng = _engine(a)
    doc = sm.load(a.file) if a.write else ""
    prior = sm.parse_tables(doc).get(a.table, {}).get("fields", {}) if doc else {}
    grain = [g.strip() for g in a.grain.split(",")] if a.grain else None
    body, facts = profile_table(eng, a.table, grain, a.layer, a.domain, prior)
    if a.write:
        Path(a.file).write_text(sm.upsert_table(doc, a.table, body))
        print(f"updated {a.file}: {a.table} ({facts['rows']:,} rows, grain {facts['grain_status']})")
    else:
        print(body)


def cmd_relate(a):
    from .relate import check, render, to_row

    r = check(_engine(a), a.child, a.parent)
    print(render(r))
    if a.write:
        doc = sm.load(a.file)
        Path(a.file).write_text(sm.upsert_relationship(doc, a.child, a.parent, to_row(r, a.note or "")))
        print(f"recorded in {a.file}")


def cmd_lint(a):
    from .lint import lint, render

    findings = lint(sm.load(a.file))
    print(render(findings))
    return 1 if any(f[0] == "ERROR" for f in findings) else 0


def cmd_qa(a):
    from .qa import render, run

    res = run(
        _engine(a), _read_sql(a.sql), [k.strip() for k in a.key.split(",")], a.anchor,
        [c.strip() for c in a.feature_times.split(",")] if a.feature_times else None,
        a.max_null_pct, a.base_sql, a.min_rows,
    )
    print(json.dumps(res, indent=2) if a.json else render(res))
    return 0 if all(r["ok"] for r in res) else 1


def cmd_signal(a):
    from .signal import analyze, render

    res = analyze(
        _engine(a), _read_sql(a.sql), a.label,
        [c.strip() for c in a.features.split(",")] if a.features else None, a.time_col, a.limit,
    )
    print(render(res))
    return 0 if any(f["verdict"] == "SIGNAL" for f in res["features"]) else 2


def cmd_diagnose(a):
    from .db import source
    from .diagnose import run

    eng = _engine(a)
    src = source(eng, a.table, _read_sql(a.sql) if a.sql else None)
    lines, flags = run(
        eng, src, a.date_col, a.value_col, a.cat_col, a.where,
        [k.strip() for k in a.key.split(",")] if a.key else None, a.expect_start, a.expect_end,
    )
    print("\n".join(lines))
    return 1 if flags else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="schemakit", description="Build and use a grounded SCHEMA.md.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, db=True):
        sp = sub.add_parser(name, help=help_)
        if db:
            sp.add_argument("--url", help="SQLAlchemy URL (or set SCHEMAKIT_URL)")
        sp.set_defaults(fn=fn)
        return sp

    s = add("init", cmd_init, "create SCHEMA.md and DOMAINS.md from templates", db=False)
    s.add_argument("--dir", default=".")
    s.add_argument("--force", action="store_true")

    s = add("inventory", cmd_inventory, "list tables, guess layer/domain, surface shared keys")
    s.add_argument("--schema", help="comma-separated schemas (default: the connection default)")
    s.add_argument("--counts", action="store_true", help="include row counts (slow on big warehouses)")
    s.add_argument("--out", help="write to a file instead of stdout")

    s = add("profile", cmd_profile, "profile a table: grain, PK, nulls, time ranges")
    s.add_argument("--table", required=True)
    s.add_argument("--grain", help="comma-separated columns you believe define one row")
    s.add_argument("--layer")
    s.add_argument("--domain")
    s.add_argument("--write", action="store_true", help="upsert into the schema file (default: print)")
    s.add_argument("--file", default="SCHEMA.md")

    s = add("relate", cmd_relate, "validate a child->parent key relationship")
    s.add_argument("--child", required=True, help="schema.table.column holding the foreign key")
    s.add_argument("--parent", required=True, help="schema.table.column holding the primary key")
    s.add_argument("--note")
    s.add_argument("--write", action="store_true")
    s.add_argument("--file", default="SCHEMA.md")

    s = add("lint", cmd_lint, "check SCHEMA.md for unverified grain, orphans, conflicts, staleness", db=False)
    s.add_argument("--file", default="SCHEMA.md")

    s = add("qa", cmd_qa, "assertions on an assembled query: grain, fan-out, leakage, nulls")
    s.add_argument("--sql", required=True, help="file with the SELECT (or - for stdin)")
    s.add_argument("--key", required=True, help="columns that must be unique per output row")
    s.add_argument("--anchor", help="the as-of / prediction timestamp column in the output")
    s.add_argument("--feature-times", help="timestamp columns of features that must be <= anchor")
    s.add_argument("--base-sql", help="scalar query for the expected row count, e.g. SELECT COUNT(*) FROM customers")
    s.add_argument("--max-null-pct", type=float, default=50.0)
    s.add_argument("--min-rows", type=int, default=1)
    s.add_argument("--json", action="store_true")

    s = add("signal", cmd_signal, "screen features against a label (permutation p, stability)")
    s.add_argument("--sql", required=True)
    s.add_argument("--label", required=True)
    s.add_argument("--features", help="comma-separated (default: all other columns)")
    s.add_argument("--time-col", help="column to split halves chronologically for a stability check")
    s.add_argument("--limit", type=int, default=200_000)

    s = add("diagnose", cmd_diagnose, "why no data/signal? coverage, gaps, percentiles, stray predicates")
    s.add_argument("--table")
    s.add_argument("--sql", help="query file instead of --table")
    s.add_argument("--date-col")
    s.add_argument("--value-col")
    s.add_argument("--cat-col", help="categorical column to inspect for placeholders/variants")
    s.add_argument("--where", help="the predicate you are filtering with; reports how many rows it removes")
    s.add_argument("--key", help="columns that should be unique")
    s.add_argument("--expect-start")
    s.add_argument("--expect-end")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a) or 0
