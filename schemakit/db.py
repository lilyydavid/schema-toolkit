"""Thin database helpers. Everything goes through SQLAlchemy so any warehouse with a driver works."""
from __future__ import annotations

from sqlalchemy import create_engine, text


def connect(url: str):
    return create_engine(url)


def query(engine, sql: str, **params) -> list[dict]:
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        return [dict(r._mapping) for r in res]


def scalar(engine, sql: str, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def quote(engine, name: str) -> str:
    """Quote a possibly-qualified name like schema.table or db.schema.table."""
    prep = engine.dialect.identifier_preparer
    return ".".join(prep.quote(p) for p in name.split("."))


def split_name(name: str) -> tuple[str | None, str]:
    if "." in name:
        schema, table = name.rsplit(".", 1)
        return schema, table
    return None, name


def month_expr(engine, col: str) -> str:
    """Dialect-specific 'bucket this timestamp into a month' expression."""
    d = engine.dialect.name
    if d == "sqlite":
        return f"strftime('%Y-%m', {col})"
    if d in ("mysql", "mariadb"):
        return f"DATE_FORMAT({col}, '%Y-%m')"
    if d == "bigquery":
        return f"FORMAT_DATE('%Y-%m', DATE({col}))"
    return f"CAST(date_trunc('month', {col}) AS DATE)"


def source(engine, table: str | None, sql: str | None) -> str:
    """Return a FROM-able source: a quoted table, or a parenthesised user query."""
    if table:
        return quote(engine, table)
    if sql:
        return f"({sql.strip().rstrip(';')}) AS q"
    raise ValueError("need --table or --sql")
