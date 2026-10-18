"""Step 7: is there any signal? Dependency-free univariate screen with permutation p-values and a stability check."""
from __future__ import annotations

import math
import random
from typing import Sequence

from sqlalchemy import text


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def _num(v):
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch(engine, sql: str, limit: int) -> tuple[list[str], list[tuple]]:
    src = f"({sql.strip().rstrip(';')}) AS q"
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT * FROM {src}"))
        cols = list(res.keys())
        rows = res.fetchmany(limit)
    return cols, rows


def bin_means(x: list[float], y: list[float], k: int = 5) -> list[tuple[float, float, int]]:
    """Quantile bins of x -> (mean x, mean y, n). Shows monotonic lift that a single r can hide."""
    order = sorted(range(len(x)), key=lambda i: x[i])
    out = []
    for b in range(k):
        idx = order[b * len(x) // k : (b + 1) * len(x) // k]
        if idx:
            out.append((sum(x[i] for i in idx) / len(idx), sum(y[i] for i in idx) / len(idx), len(idx)))
    return out


def analyze(engine, sql: str, label: str, features: list[str] | None = None, time_col: str | None = None,
            limit: int = 200_000, perms: int = 200, seed: int = 7) -> dict:
    cols, rows = fetch(engine, sql, limit)
    if label not in cols:
        raise SystemExit(f"label column '{label}' not in query output: {cols}")
    li = cols.index(label)
    ti = cols.index(time_col) if time_col else None
    skip = {label, time_col}
    cand = features or [c for c in cols if c not in skip]
    rng = random.Random(seed)
    out = []
    for f in cand:
        if f not in cols:
            continue
        fi = cols.index(f)
        pairs = [(_num(r[fi]), _num(r[li]), r[ti] if ti is not None else None) for r in rows]
        pairs = [p for p in pairs if p[0] is not None and p[1] is not None]
        n_total = len(rows)
        if len(pairs) < 30 or len({p[0] for p in pairs}) < 2:
            out.append({"feature": f, "n": len(pairs), "r": 0.0, "p": 1.0, "stable": None, "verdict": "UNUSABLE (constant or <30 rows)",
                        "coverage": len(pairs) / n_total if n_total else 0})
            continue
        x, y = [p[0] for p in pairs], [p[1] for p in pairs]
        r = pearson(x, y)
        sub = rng.sample(range(len(x)), min(len(x), 20_000))
        xs, ys = [x[i] for i in sub], [y[i] for i in sub]
        r_sub = abs(pearson(xs, ys))
        ge = 0
        yp = ys[:]
        for _ in range(perms):
            rng.shuffle(yp)
            if abs(pearson(xs, yp)) >= r_sub:
                ge += 1
        p = (ge + 1) / (perms + 1)
        stable = None
        if ti is not None:
            ordered = sorted(pairs, key=lambda q: str(q[2]))
            half = len(ordered) // 2
            r1 = pearson([q[0] for q in ordered[:half]], [q[1] for q in ordered[:half]])
            r2 = pearson([q[0] for q in ordered[half:]], [q[1] for q in ordered[half:]])
            stable = (r1 * r2 > 0) and min(abs(r1), abs(r2)) >= 0.5 * abs(r)
        if abs(r) >= 0.05 and p <= 0.01 and stable is not False:
            verdict = "SIGNAL"
        elif abs(r) >= 0.02 and p <= 0.05:
            verdict = "weak"
        else:
            verdict = "none"
        out.append({"feature": f, "n": len(pairs), "r": r, "p": p, "stable": stable, "verdict": verdict,
                    "coverage": len(pairs) / n_total if n_total else 0, "bins": bin_means(x, y)})
    out.sort(key=lambda d: -abs(d["r"]))
    base = [v for v in (_num(r[li]) for r in rows) if v is not None]
    return {"rows": len(rows), "base_rate": sum(base) / len(base) if base else float("nan"), "features": out}


def render(a: dict) -> str:
    L = [f"rows analysed: {a['rows']:,}   label mean: {a['base_rate']:.4f}", "",
         f"{'feature':28} {'n':>8} {'cov':>5} {'r':>8} {'perm p':>7} {'stable':>7}  verdict"]
    for f in a["features"]:
        st = "-" if f["stable"] is None else ("yes" if f["stable"] else "NO")
        L.append(f"{f['feature'][:28]:28} {f['n']:>8,} {f['coverage']*100:>4.0f}% {f['r']:>8.3f} {f['p']:>7.3f} {st:>7}  {f['verdict']}")
    top = [f for f in a["features"] if f.get("bins") and f["verdict"] == "SIGNAL"][:3]
    for f in top:
        L.append(f"\nquintile lift for {f['feature']} (label mean by feature bin, low→high):")
        L.append("  " + "  ".join(f"{b[1]:.3f}" for b in f["bins"]))
    if not any(f["verdict"] == "SIGNAL" for f in a["features"]):
        L += ["", "NO SIGNAL FOUND. Do not conclude 'no relationship' yet: run `schemakit diagnose` on the dataset",
              "(date coverage, percentiles, stray predicates, trend breaks) before accepting the null."]
    return "\n".join(L)
