"""Step 8: why might there be no data/signal? Date ranges, gaps, percentiles, nulls, stray predicates, trend breaks."""
from __future__ import annotations

import datetime as dt
import statistics

from sqlalchemy import text

from .db import month_expr, query, scalar

SENTINEL_STRINGS = {"", "test", "tests", "n/a", "na", "null", "none", "unknown", "undefined", "tbd", "-", "(blank)", "dummy"}


def _pctile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def run(engine, src: str, date_col: str | None, value_col: str | None = None, cat_col: str | None = None,
        where: str | None = None, key: list[str] | None = None, expect_start: str | None = None,
        expect_end: str | None = None, sample: int = 500_000) -> tuple[list[str], list[str]]:
    """Return (report lines, red flags)."""
    prep = engine.dialect.identifier_preparer
    q = prep.quote
    out: list[str] = []
    flags: list[str] = []
    n = scalar(engine, f"SELECT COUNT(*) FROM {src}")
    out += [f"# Diagnostics", "", f"Total rows: {n:,}"]
    if n == 0:
        flags.append("source is EMPTY; check upstream load, permissions, or a wrong table/schema")
        return out, flags

    if where:
        kept = scalar(engine, f"SELECT COUNT(*) FROM {src} WHERE {where}")
        out.append(f"Rows surviving your predicate `{where}`: {kept:,} ({100*kept/n:.1f}%)")
        if kept == 0:
            flags.append("your WHERE clause removes every row; a stray or mistyped predicate is the likeliest cause")
            out += ["", "Stopped: nothing left to inspect. Run again without --where, and with --cat-col on the filtered column to see its real values."]
            out += ["", "## Red flags"] + [f"- {f}" for f in flags]
            return out, flags
        elif kept / n < 0.1:
            flags.append(f"predicate keeps only {100*kept/n:.1f}% of rows; confirm that is intended")
    base = f"{src} WHERE {where}" if where else src

    # ---- Dates
    if date_col:
        d = q(date_col)
        r0 = query(engine, f"SELECT MIN({d}) mn, MAX({d}) mx, COUNT({d}) nn FROM {base}")[0]
        mn, mx, nn = r0["mn"], r0["mx"], r0["nn"]
        out += ["", "## Date coverage", f"- `{date_col}` range: {mn} → {mx}  (non-null: {nn:,})"]
        if nn == 0:
            flags.append(f"{date_col} is entirely NULL")
        else:
            if expect_start and str(mn)[:10] > expect_start:
                flags.append(f"data starts {str(mn)[:10]}, later than the expected {expect_start}")
            if expect_end and str(mx)[:10] < expect_end:
                flags.append(f"data ends {str(mx)[:10]}, earlier than the expected {expect_end}; stale or partial load")
            today = dt.date.today().isoformat()
            if str(mx)[:10] > today:
                flags.append(f"{date_col} has future dates (max {str(mx)[:10]})")
            try:
                if (dt.date.fromisoformat(today) - dt.date.fromisoformat(str(mx)[:10])).days > 45 and not expect_end:
                    flags.append(f"latest {date_col} is {str(mx)[:10]}; data may be stale (pass --expect-end to be explicit)")
            except ValueError:
                pass
            bad = scalar(engine, f"SELECT COUNT(*) FROM {base}{' AND' if where else ' WHERE'} ({d} < '1971-01-01' OR {d} > '2100-01-01')")
            if bad:
                flags.append(f"{bad:,} rows have sentinel-looking dates in {date_col} (<1971 or >2100: epoch zero / 9999 placeholders)")
            m = month_expr(engine, d)
            vexpr = f", COUNT({q(value_col)}) vn, AVG(CAST({q(value_col)} AS FLOAT)) vavg" if value_col else ""
            months = query(engine, f"SELECT {m} AS m, COUNT(*) c{vexpr} FROM {base}{' AND' if where else ' WHERE'} {d} IS NOT NULL GROUP BY 1 ORDER BY 1")
            counts = [r["c"] for r in months]
            med = statistics.median(counts)
            out += ["", "| month | rows | " + ("non-null value | mean value |" if value_col else ""), "|---|---|" + ("---|---|" if value_col else "")]
            for r in months:
                mark = " ⚠" if r["c"] < 0.2 * med else ""
                extra = f" {r['vn']:,} | {r['vavg']:.3f} |" if value_col and r["vavg"] is not None else (" 0 | |" if value_col else "")
                out.append(f"| {r['m']}{mark} | {r['c']:,} |{extra}")
            thin = [str(r["m"]) for r in months if r["c"] < 0.2 * med]
            if thin:
                flags.append(f"months with <20% of median volume (partial load or outage?): {', '.join(thin[:6])}")
            ys = sorted({str(r["m"]) for r in months})
            if len(ys) >= 2 and len(ys) < 100:
                have = {str(r["m"])[:7] for r in months}
                y0, m0 = int(ys[0][:4]), int(ys[0][5:7])
                y1, m1 = int(ys[-1][:4]), int(ys[-1][5:7])
                gaps, y, mo = [], y0, m0
                while (y, mo) <= (y1, m1):
                    k = f"{y:04d}-{mo:02d}"
                    if k not in have:
                        gaps.append(k)
                    mo += 1
                    if mo == 13:
                        y, mo = y + 1, 1
                if gaps:
                    flags.append(f"months with ZERO rows inside the range: {', '.join(gaps[:8])}")
            if value_col and len(months) >= 4:
                means = [(str(r["m"]), r["vavg"]) for r in months if r["vavg"] is not None]
                steps = [(means[i][0], abs(means[i][1] - means[i - 1][1])) for i in range(1, len(means))]
                diffs = [s[1] for s in steps]
                if diffs:
                    mad = statistics.median(abs(x - statistics.median(diffs)) for x in diffs) or 1e-9
                    worst = max(steps, key=lambda s: s[1])
                    if (worst[1] - statistics.median(diffs)) / mad > 6:
                        flags.append(f"trend break: mean of {value_col} jumps most at {worst[0]} (step {worst[1]:.3f}); look for a definition/pipeline change")

    # ---- Value distribution
    if value_col:
        v = q(value_col)
        nulls = scalar(engine, f"SELECT COUNT(*) FROM {base}{' AND' if where else ' WHERE'} {v} IS NULL")
        zeros = scalar(engine, f"SELECT COUNT(*) FROM {base}{' AND' if where else ' WHERE'} {v} = 0")
        out += ["", f"## Distribution of `{value_col}`", f"- nulls: {nulls:,}  zeros: {zeros:,}"]
        if nulls / n > 0.5:
            flags.append(f"{value_col} is {100*nulls/n:.0f}% NULL")
        if zeros / n > 0.5:
            flags.append(f"{value_col} is {100*zeros/n:.0f}% zeros (often a default fill, not a measurement)")
        with engine.connect() as conn:
            cond = f" AND ({where})" if where else ""
            vals = [float(r[0]) for r in conn.execute(text(f"SELECT {v} FROM {src} WHERE {v} IS NOT NULL{cond}")).fetchmany(sample)]
        if vals:
            vals.sort()
            pts = [0, 1, 5, 25, 50, 75, 95, 99, 100]
            ps = {p: _pctile(vals, p) for p in pts}
            out.append("- percentiles: " + "  ".join(f"p{p}={ps[p]:.4g}" for p in pts))
            if ps[1] == ps[99]:
                flags.append(f"{value_col}: p1 == p99; effectively constant, so no signal is possible")
            elif ps[25] == ps[75]:
                flags.append(f"{value_col}: p25 == p75; >50% of mass on one value, so signal lives in a thin tail")
            if ps[95] and ps[99] > 10 * abs(ps[95]) and ps[95] != 0:
                flags.append(f"{value_col}: p99 is >10× p95; outliers will dominate means and correlations (winsorize or use ranks)")
            if ps[0] < 0 and ps[1] >= 0:
                flags.append(f"{value_col}: a few negative values (min {ps[0]:.4g}) amid non-negative data; refunds/reversals or errors?")

    # ---- Stray predicates / categorical hygiene
    if cat_col:
        c = q(cat_col)
        top = query(engine, f"SELECT {c} AS v, COUNT(*) c FROM {base} GROUP BY {c} ORDER BY c DESC")
        out += ["", f"## Values of `{cat_col}` ({len(top)} distinct)"]
        for r in top[:15]:
            out.append(f"- `{r['v']}`: {r['c']:,} ({100*r['c']/n:.1f}%)")
        norm: dict[str, list] = {}
        for r in top:
            k = str(r["v"]).strip().lower()
            norm.setdefault(k, []).append(r["v"])
            if k in SENTINEL_STRINGS and r["v"] is not None and r["c"] / n > 0.005:
                flags.append(f"{cat_col}='{r['v']}' holds {100*r['c']/n:.1f}% of rows; placeholder/test value mixing into the signal")
        dup_variants = {k: v for k, v in norm.items() if len(v) > 1}
        if dup_variants:
            flags.append(f"{cat_col} has case/whitespace variants of the same value: {list(dup_variants.values())[:3]}; equality predicates will silently miss rows")
        nnull = sum(r["c"] for r in top if r["v"] is None)
        if nnull / n > 0.2:
            flags.append(f"{cat_col} is {100*nnull/n:.0f}% NULL; a predicate on it drops those rows (NULL != anything)")

    # ---- Duplicates
    if key:
        kc = ", ".join(q(k) for k in key)
        dups = scalar(engine, f"SELECT COUNT(*) FROM (SELECT {kc} FROM {base} GROUP BY {kc} HAVING COUNT(*) > 1) d")
        out += ["", f"## Duplicates on ({', '.join(key)}): {dups:,}"]
        if dups:
            flags.append(f"{dups:,} duplicated keys on ({', '.join(key)}); duplicates over-weight some entities and inflate apparent signal")

    out += ["", "## Red flags"] + ([f"- {f}" for f in flags] or ["- none; the data looks structurally healthy. If there is still no signal, the null result may be real."])
    return out, flags
