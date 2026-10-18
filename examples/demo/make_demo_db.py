"""Build a small SQLite warehouse with realistic traps so you can practise the workflow.

Usage: python examples/demo/make_demo_db.py examples/demo/demo.db

Traps planted on purpose (each is something `schemakit` should surface):
  * silver_events.customer_id has ~3% orphans (ids that exist in no customer table)
  * silver_invoices.customer_id is TEXT while silver_customers.customer_id is INTEGER
  * silver_invoices has ~1% duplicated invoice_id rows (stated grain is violated)
  * silver_events has a pipeline outage: zero rows for 2025-08
  * silver_tickets.status has case/whitespace variants ('open', 'OPEN ', 'Open')
  * silver_customers has internal test accounts (is_test = 1) that skew behaviour
  * gold_customers twin of silver_customers (which one is canonical?)
  * a REAL signal: low recent activity + recent tickets => churn within 60 days
"""
from __future__ import annotations

import datetime as dt
import math
import random
import sqlite3
import sys

SEED = 42
END = dt.datetime(2026, 6, 30)
ANCHOR = dt.datetime(2025, 12, 31)  # the demo prediction date
N = 2000


def poisson(rng: random.Random, lam: float) -> int:
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def ts(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def main(path: str) -> None:
    rng = random.Random(SEED)
    con = sqlite3.connect(path)
    con.executescript(
        """
        DROP TABLE IF EXISTS silver_customers; DROP TABLE IF EXISTS gold_customers;
        DROP TABLE IF EXISTS silver_subscriptions; DROP TABLE IF EXISTS silver_invoices;
        DROP TABLE IF EXISTS silver_events; DROP TABLE IF EXISTS silver_tickets;
        CREATE TABLE silver_customers(customer_id INTEGER PRIMARY KEY, email TEXT, signup_at TIMESTAMP, plan_tier TEXT, is_test INTEGER);
        CREATE TABLE gold_customers(customer_id INTEGER, plan_tier TEXT, lifetime_value REAL, updated_at TIMESTAMP);
        CREATE TABLE silver_subscriptions(subscription_id INTEGER PRIMARY KEY, customer_id INTEGER, plan TEXT, started_at TIMESTAMP, ended_at TIMESTAMP);
        CREATE TABLE silver_invoices(invoice_id TEXT, subscription_id INTEGER, customer_id TEXT, amount REAL, invoiced_at TIMESTAMP, loaded_at TIMESTAMP);
        CREATE TABLE silver_events(event_id INTEGER PRIMARY KEY, customer_id INTEGER, event_type TEXT, event_ts TIMESTAMP);
        CREATE TABLE silver_tickets(ticket_id INTEGER PRIMARY KEY, customer_id INTEGER, opened_at TIMESTAMP, severity TEXT, status TEXT);
        """
    )
    prices = {"basic": 10.0, "pro": 30.0, "team": 90.0}
    customers, subs, invoices, events, tickets, gold = [], [], [], [], [], []
    event_id = ticket_id = 1
    inv_n = 1
    for cid in range(1, N + 1):
        is_test = 1 if cid % 97 == 0 else 0
        signup = dt.datetime(2024, 1, 1) + dt.timedelta(days=rng.randint(0, 600), hours=rng.randint(0, 23))
        plan = rng.choices(list(prices), [0.6, 0.3, 0.1])[0]
        email = f"test+{cid}@acme.com" if is_test else f"user{cid}@example.com"
        customers.append((cid, email, ts(signup), plan.upper() if cid % 11 == 0 else plan, is_test))
        e = rng.gauss(0, 1)  # latent engagement
        started = signup + dt.timedelta(days=rng.randint(0, 5))
        ended = None
        if rng.random() < 0.15:  # early churners, before the anchor
            span = (ANCHOR - started).days
            if span > 30:
                ended = started + dt.timedelta(days=rng.randint(20, span))
        will_churn = False
        if ended is None and started < ANCHOR:
            recent_tickets_pressure = rng.random() < 0.25
            p = 1 / (1 + math.exp(-(-1.4 - 1.1 * e + (0.9 if recent_tickets_pressure else 0))))
            if rng.random() < p:
                will_churn = True
                ended = ANCHOR + dt.timedelta(days=rng.randint(1, 60), hours=rng.randint(0, 23))
        else:
            recent_tickets_pressure = False
        subs.append((cid, cid, plan, ts(started), ts(ended) if ended else None))
        stop = ended or END
        rate = 0.12 * math.exp(0.6 * e)
        # engagement fades in the 30 days before a churn (the real signal lives in the last month)
        d = started
        while d < stop:
            lam = rate * (0.4 if will_churn and d > ANCHOR - dt.timedelta(days=30) else 1.0)
            for _ in range(poisson(rng, lam)):
                when = d + dt.timedelta(seconds=rng.randint(0, 86399))
                if when >= stop or (when.year, when.month) == (2025, 8):  # outage month
                    continue
                cust = cid if rng.random() > 0.03 else rng.randint(9_000_000, 9_000_500)  # orphans
                events.append((event_id, cust, rng.choice(["login", "view", "create", "share"]), ts(when)))
                event_id += 1
            d += dt.timedelta(days=1)
        t_rate = 0.01 + (0.06 if recent_tickets_pressure else 0)
        d = started
        while d < stop:
            if rng.random() < t_rate and d <= ANCHOR:
                status = rng.choice(["open", "OPEN ", "Open", "closed", "Closed"])
                tickets.append((ticket_id, cid, ts(d + dt.timedelta(hours=rng.randint(0, 23))), rng.choice(["low", "med", "high"]), status))
                ticket_id += 1
            d += dt.timedelta(days=1)
        # monthly invoices until the end of the subscription
        m = started
        while m < stop:
            inv = (f"INV{inv_n:07d}", cid, str(cid), prices[plan], ts(m), ts(m + dt.timedelta(days=2)))
            invoices.append(inv)
            if rng.random() < 0.01:
                invoices.append(inv)  # duplicated load
            inv_n += 1
            m += dt.timedelta(days=30)
        gold.append((cid, plan, round(prices[plan] * rng.randint(1, 18), 2), ts(END)))
    con.executemany("INSERT INTO silver_customers VALUES (?,?,?,?,?)", customers)
    con.executemany("INSERT INTO gold_customers VALUES (?,?,?,?)", gold)
    con.executemany("INSERT INTO silver_subscriptions VALUES (?,?,?,?,?)", subs)
    con.executemany("INSERT INTO silver_invoices VALUES (?,?,?,?,?,?)", invoices)
    con.executemany("INSERT INTO silver_events VALUES (?,?,?,?)", events)
    con.executemany("INSERT INTO silver_tickets VALUES (?,?,?,?,?)", tickets)
    con.commit()
    for t in ["silver_customers", "silver_subscriptions", "silver_invoices", "silver_events", "silver_tickets", "gold_customers"]:
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "demo.db")
