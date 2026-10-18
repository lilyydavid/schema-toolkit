"""Read, upsert and parse SCHEMA.md.

Machine-owned regions are fenced by HTML comments so humans can add notes around them
and re-profiling never clobbers what you wrote.
"""
from __future__ import annotations

import re
from pathlib import Path

TABLES_END = "<!-- schemakit:tables-end -->"
RELS_END = "<!-- schemakit:relationships-end -->"
TEMPLATES = Path(__file__).parent / "templates"

HUMAN_NOTES = """**Human notes**
- **Time semantics:** _(event time vs load time? timezone? typical lateness?)_
- **Safe window:** _(earliest/latest date you trust; any backfill or partial months)_
- **Gotchas:** _(test accounts, soft deletes, dup keys, conflicting twin tables)_
"""


def template(name: str) -> str:
    return (TEMPLATES / name).read_text()


def load(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path} not found. Run `schemakit init` first.")
    return p.read_text()


def _begin(name: str) -> str:
    return f"<!-- schemakit:begin {name} -->"


def _end(name: str) -> str:
    return f"<!-- schemakit:end {name} -->"


def upsert_table(doc: str, name: str, body: str) -> str:
    """Replace the machine region for `name`, or add a new section for it."""
    region = f"{_begin(name)}\n{body.strip()}\n{_end(name)}"
    pat = re.compile(re.escape(_begin(name)) + r".*?" + re.escape(_end(name)), re.S)
    if pat.search(doc):
        return pat.sub(lambda _: region, doc)
    section = f"### `{name}`\n{region}\n\n{HUMAN_NOTES}\n"
    if TABLES_END not in doc:
        raise SystemExit("SCHEMA.md is missing the tables-end marker; re-run `schemakit init` or restore it.")
    return doc.replace(TABLES_END, section + TABLES_END)


def upsert_relationship(doc: str, child: str, parent: str, row: str) -> str:
    lines = doc.splitlines()
    key = f"| `{child}` | `{parent}` |"
    for i, ln in enumerate(lines):
        if ln.startswith(key):
            lines[i] = row
            return "\n".join(lines) + ("\n" if doc.endswith("\n") else "")
    if RELS_END not in doc:
        raise SystemExit("SCHEMA.md is missing the relationships-end marker.")
    return doc.replace(RELS_END, row + "\n" + RELS_END)


_FIELD = re.compile(r"^- \*\*(.+?):\*\*\s*(.*)$")


def parse_tables(doc: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in re.finditer(r"<!-- schemakit:begin (.+?) -->\n(.*?)\n<!-- schemakit:end \1 -->", doc, re.S):
        name, body = m.group(1), m.group(2)
        fields, cols = {}, []
        for ln in body.splitlines():
            fm = _FIELD.match(ln)
            if fm:
                fields[fm.group(1).strip().lower()] = fm.group(2).strip()
            elif ln.startswith("| `"):
                cells = [c.strip() for c in ln.strip("|").split("|")]
                cols.append({"name": cells[0].strip("`"), "type": cells[1]})
        out[name] = {"fields": fields, "columns": cols}
    return out


def parse_relationships(doc: str) -> list[dict]:
    rels = []
    for ln in doc.splitlines():
        if ln.startswith("| `"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            # Column-table rows also start with "| `". Relationship rows have a backticked,
            # dotted child.col in cell 0 and parent.col in cell 1.
            if len(cells) >= 6 and cells[1].startswith("`") and "." in cells[0] and "." in cells[1]:
                rels.append(
                    {
                        "child": cells[0].strip("`"),
                        "parent": cells[1].strip("`"),
                        "cardinality": cells[2],
                        "match": cells[3],
                        "orphan": cells[4],
                        "verified": cells[5],
                    }
                )
    return rels


def pct(s: str) -> float | None:
    m = re.search(r"-?\d+(\.\d+)?", s or "")
    return float(m.group()) if m else None
