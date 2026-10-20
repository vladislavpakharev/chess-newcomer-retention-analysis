"""Builds the SQLite database used by the analysis.

Tables created by connect():

  users      user_id, signup_date
  activity   one row = one user on one day they visited:
             user_id, date, games, wins, puzzles, lessons
  act        activity + signup_date, signup_month, day_n (0 = registration day),
             week (Monday of the week), month
  newcomers  one row per user who registered on/after the first day of the export:
             what they did on day 0 (games0, wins0, puzzles0, lessons0) and
             retention flags back_d1, back_d7, back_w1, days_30, full_week, full_month.
             Newcomers of the last days have an unfinished week/month: filter
             with full_week = 1 / full_month = 1 when comparing retention.
  cohorts    the cohort report from data/cohort_report.csv: cohort, d0 ... d30
             (an empty cell = that day has not happened yet -> NULL)

Run `python3 src/build_db.py` to print row counts.
"""

import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

PREPARE = """
CREATE INDEX activity_user ON activity(user_id, date);

CREATE TABLE act AS
SELECT a.*,
       u.signup_date,
       substr(u.signup_date, 1, 7)                                           AS signup_month,
       CAST(julianday(a.date) - julianday(u.signup_date) AS INTEGER)         AS day_n,
       date(a.date, '-6 days', 'weekday 1')                                  AS week,
       substr(a.date, 1, 7)                                                  AS month
FROM activity a JOIN users u ON u.user_id = a.user_id
ORDER BY a.date, a.user_id;

CREATE TABLE newcomers AS
SELECT u.user_id, u.signup_date, substr(u.signup_date, 1, 7) AS signup_month,
       a.games AS games0, a.wins AS wins0, a.puzzles AS puzzles0, a.lessons AS lessons0,
       EXISTS (SELECT 1 FROM activity b WHERE b.user_id = u.user_id
               AND b.date = date(u.signup_date, '+1 day'))                    AS back_d1,
       EXISTS (SELECT 1 FROM activity b WHERE b.user_id = u.user_id
               AND b.date = date(u.signup_date, '+7 days'))                   AS back_d7,
       EXISTS (SELECT 1 FROM activity b WHERE b.user_id = u.user_id
               AND b.date BETWEEN date(u.signup_date, '+1 day')
                              AND date(u.signup_date, '+7 days'))             AS back_w1,
       (SELECT COUNT(*) FROM activity b WHERE b.user_id = u.user_id
               AND b.date BETWEEN date(u.signup_date, '+1 day')
                              AND date(u.signup_date, '+30 days'))            AS days_30,
       date(u.signup_date, '+7 days')  <= (SELECT MAX(date) FROM activity)    AS full_week,
       date(u.signup_date, '+30 days') <= (SELECT MAX(date) FROM activity)    AS full_month
FROM users u
JOIN activity a ON a.user_id = u.user_id AND a.date = u.signup_date
WHERE u.signup_date >= (SELECT MIN(date) FROM activity)
ORDER BY u.user_id;
"""


def _load_table(con, table, filename, columns):
    """Load a CSV into a table. An empty cell becomes NULL; INTEGER columns become ints."""
    ddl = ", ".join("%s %s" % (name, kind) for name, kind in columns)
    con.execute("CREATE TABLE %s (%s)" % (table, ddl))
    rows = []
    with open(DATA_DIR / filename, encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        next(reader)  # header
        for row in reader:
            values = []
            for (name, kind), cell in zip(columns, row):
                if cell == "":
                    values.append(None)
                elif kind.startswith("INTEGER"):
                    values.append(int(cell))
                else:
                    values.append(cell)
            rows.append(values)
    marks = ", ".join("?" for _ in columns)
    con.executemany("INSERT INTO %s VALUES (%s)" % (table, marks), rows)


def connect(path=":memory:"):
    """Return a connection with all tables described above."""
    con = sqlite3.connect(path)
    _load_table(con, "users", "users.csv",
                [("user_id", "INTEGER PRIMARY KEY"), ("signup_date", "TEXT")])
    _load_table(con, "activity", "activity.csv",
                [("user_id", "INTEGER"), ("date", "TEXT"), ("games", "INTEGER"),
                 ("wins", "INTEGER"), ("puzzles", "INTEGER"), ("lessons", "INTEGER")])
    _load_table(con, "cohorts", "cohort_report.csv",
                [("cohort", "TEXT")] + [("d%d" % k, "INTEGER") for k in range(31)])
    con.executescript(PREPARE)
    con.commit()
    return con


if __name__ == "__main__":
    connection = connect()
    for name in ("users", "activity", "act", "newcomers", "cohorts"):
        count = connection.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
        print("%s: %d rows" % (name, count))
