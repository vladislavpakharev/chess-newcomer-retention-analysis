# Chess Website: Newcomer Retention Analysis

Product-analytics case: a chess website had a record month of traffic (July–September
2026, ≈25k users, ≈208k user-days), but are the new users staying? The analysis moves from
"is this a record or a problem?" to a ranked list of hypotheses about why newcomers leave.
Everything is plain SQL (SQLite) driven from Python. Reports are written in Russian.

## Key findings

- **Growth was bought with low-quality traffic.** MAU rose from 7,917 (July) to 17,805
  (August), but average-DAU/MAU "stickiness" fell from 20.4 % to 14.9 %. The cause is
  newcomers: their stickiness dropped to 8.9 %, while existing users stayed flat (≈26 %).
  Had August newcomers retained like July's, ≈2,000 more people would have returned in September.
- **Two registration waves.** 15 cohorts (7–16 Aug and 28 Aug–1 Sep) were more than twice
  the usual size. They hold 49.8 % of all newcomers and retain far worse
  (D1 / D7 / D30: 21.8 % / 9.4 % / 3.6 % vs 39.6 % / 22.8 % / 10.9 % for the rest).
- **A single-day anomaly** on 19 Aug (DAU 935 vs ≈2,500 on neighbouring days) hits old
  users too, so it is a site-wide event, not a cohort effect.
- **Hypotheses, tested against the data** (with the honest alternative explanation for each):
  - *H1, a loss is a dead end:* newcomers with no win on day 0 return within a week far less
    often (25.7 % vs 60.2 %); the gap persists inside every wave. Strongest hypothesis.
  - *H3, learning is hidden:* newcomers who did a puzzle/lesson on day 0 return more often
    (+7–13 pp), but keen users may simply self-select.
  - *H2 (first game too fast) and H4 (first rating is wrong)* cannot be tested with this data:
    time controls and ratings are not in the export.

## Repository

```
reports/01_metrics.md              DAU / WAU / MAU, stickiness, newcomers vs. old users
reports/02_cohort_report.md        reading a cohort table, waves, retention in %
reports/03_why_newcomers_leave.md  newcomer journey, signals, hypotheses, honesty check
src/build_db.py                    CSV -> SQLite, builds act, newcomers, cohorts
src/sqlmd.py                       runs every ```sql block of a report and prints results
tests/                             database checks + every report's SQL must run
data/                              synthetic course data (see data/NOTICE.md)
```

## Run it

Python 3.9+, standard library only.

```bash
python3 src/build_db.py
python3 src/sqlmd.py reports/01_metrics.md
python3 -m unittest discover -s tests -v
```

## Method notes

- Each report item follows *question → answer in numbers → SQL*; claims that are a guess
  about a cause are marked as such, and "newcomer" is defined explicitly (registered on or
  after 1 July 2026, the only users whose full history is visible).
- Retention for newcomers is computed only where the whole week/month is inside the export
  (`full_week` / `full_month`), otherwise recent cohorts would look artificially bad.
- Context: a learning case from the School 21 data-analysis intensive. Later steps of the
  original case (RICE prioritisation, a wireframe, a prototype) are not part of this repository.
