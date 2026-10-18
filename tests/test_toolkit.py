import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemakit import diagnose, lint, profile, qa, relate, schema_md as sm, signal  # noqa: E402
from schemakit.db import connect, source  # noqa: E402


def make_db(path):
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, created_at TIMESTAMP, segment TEXT);
        CREATE TABLE orders(order_id INTEGER, customer_id INTEGER, ordered_at TIMESTAMP, amount REAL);
        """
    )
    for i in range(1, 201):
        con.execute("INSERT INTO customers VALUES (?,?,?)", (i, "2024-01-01 00:00:00", "A" if i % 2 else "a "))
    rows = []
    for i in range(1, 401):
        cid = 1 + (i % 200) if i % 20 else 9999  # 5% orphans
        rows.append((i, cid, f"2024-0{1 + i % 6}-15 00:00:00", float(i % 7)))
    rows.append(rows[0])  # one duplicate order row
    con.executemany("INSERT INTO orders VALUES (?,?,?,?)", rows)
    con.commit()
    con.close()


class ToolkitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.dbp = os.path.join(cls.tmp, "t.db")
        make_db(cls.dbp)
        cls.eng = connect(f"sqlite:///{cls.dbp}")

    def test_profile_verifies_and_violates_grain(self):
        body, facts = profile.profile_table(self.eng, "customers")
        self.assertIn("customer_id", body)
        self.assertTrue(facts["grain_status"].startswith("inferred"))
        _, facts = profile.profile_table(self.eng, "orders", grain=["order_id"])
        self.assertTrue(facts["grain_status"].startswith("VIOLATED"))

    def test_relate_finds_orphans(self):
        r = relate.check(self.eng, "orders.customer_id", "customers.customer_id")
        self.assertEqual(r["cardinality"], "many:1")
        self.assertEqual(r["orphans"], 20)
        self.assertAlmostEqual(r["orphan_pct"], 100 * 20 / 401, places=1)

    def test_schema_md_roundtrip_and_lint(self):
        doc = sm.template("SCHEMA.template.md")
        for t, grain in [("customers", None), ("orders", ["order_id"])]:
            body, _ = profile.profile_table(self.eng, t, grain)
            doc = sm.upsert_table(doc, t, body)
        # re-profiling replaces the region instead of duplicating it
        body, _ = profile.profile_table(self.eng, "customers")
        doc = sm.upsert_table(doc, "customers", body)
        self.assertEqual(doc.count("schemakit:begin customers"), 1)
        r = relate.check(self.eng, "orders.customer_id", "customers.customer_id")
        doc = sm.upsert_relationship(doc, r["child"], r["parent"], relate.to_row(r))
        doc = sm.upsert_relationship(doc, r["child"], r["parent"], relate.to_row(r))
        self.assertEqual(len(sm.parse_relationships(doc)), 1)
        msgs = [f for f in lint.lint(doc) if f[0] == "ERROR"]
        self.assertTrue(any("grain is violated" in m[2] for m in msgs))

    def test_qa_detects_fanout_and_leakage(self):
        sql = (
            "SELECT c.customer_id, '2024-03-01 00:00:00' AS anchor, o.ordered_at AS last_order_ts "
            "FROM customers c JOIN orders o ON o.customer_id = c.customer_id"
        )
        res = {r["check"]: r for r in qa.run(self.eng, sql, ["customer_id"], "anchor", ["last_order_ts"])}
        self.assertFalse(res["grain_unique"]["ok"])
        self.assertFalse(res["no_leakage[last_order_ts]"]["ok"])

    def test_signal_finds_planted_signal_and_rejects_noise(self):
        con = sqlite3.connect(self.dbp)
        con.execute("DROP TABLE IF EXISTS s")
        con.execute("CREATE TABLE s(x REAL, noise REAL, y REAL, t TEXT)")
        import random

        rng = random.Random(1)
        for i in range(2000):
            x, n = rng.random(), rng.random()
            con.execute("INSERT INTO s VALUES (?,?,?,?)", (x, n, 1.0 if rng.random() < 0.2 + 0.6 * x else 0.0, f"2024-{1 + i % 12:02d}-01"))
        con.commit()
        con.close()
        a = signal.analyze(self.eng, "SELECT * FROM s", "y", time_col="t")
        v = {f["feature"]: f["verdict"] for f in a["features"]}
        self.assertEqual(v["x"], "SIGNAL")
        self.assertNotEqual(v["noise"], "SIGNAL")

    def test_diagnose_flags_stray_predicate_and_variants(self):
        src = source(self.eng, "orders", None)
        _, flags = diagnose.run(self.eng, src, "ordered_at", where="amount > 1000")
        self.assertTrue(any("removes every row" in f for f in flags))
        _, flags = diagnose.run(self.eng, source(self.eng, "customers", None), "created_at", cat_col="segment")
        self.assertTrue(any("variants" in f for f in flags))


if __name__ == "__main__":
    unittest.main()
