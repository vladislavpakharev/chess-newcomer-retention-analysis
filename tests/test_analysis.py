import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_db import connect  # noqa: E402
import sqlmd  # noqa: E402


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = connect()

    def one(self, sql):
        return self.con.execute(sql).fetchone()[0]

    def test_table_sizes(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM users"), 24907)
        self.assertEqual(self.one("SELECT COUNT(*) FROM newcomers"), 20907)
        self.assertEqual(self.one("SELECT COUNT(*) FROM cohorts"), 90)

    def test_period_of_the_export(self):
        self.assertEqual(self.con.execute("SELECT MIN(date), MAX(date) FROM activity").fetchone(),
                         ("2026-07-01", "2026-09-28"))

    def test_day_number_counts_from_registration(self):
        self.assertEqual(self.one("SELECT MIN(day_n) FROM act WHERE signup_date >= '2026-07-01'"), 0)

    def test_empty_cohort_cells_are_null(self):
        self.assertIsNotNone(self.one("SELECT COUNT(*) FROM cohorts WHERE d30 IS NULL"))
        self.assertEqual(self.one("SELECT d30 IS NULL FROM cohorts ORDER BY cohort DESC LIMIT 1"), 1)

    def test_full_week_filter_removes_unfinished_weeks(self):
        self.assertLess(self.one("SELECT SUM(full_week) FROM newcomers"),
                        self.one("SELECT COUNT(*) FROM newcomers"))

    def test_headline_numbers_of_the_report(self):
        self.assertEqual(self.one("SELECT COUNT(DISTINCT user_id) FROM act WHERE date = '2026-08-08'"), 3901)
        self.assertEqual(self.one("SELECT COUNT(DISTINCT user_id) FROM act WHERE month = '2026-07'"), 7917)


class ReportTests(unittest.TestCase):
    def test_every_sql_block_of_every_report_runs(self):
        for name in ("01_metrics", "02_cohort_report", "03_why_newcomers_leave"):
            with contextlib.redirect_stdout(io.StringIO()):
                code = sqlmd.run(ROOT / "reports" / (name + ".md"))
            self.assertEqual(code, 0, name)


if __name__ == "__main__":
    unittest.main()
