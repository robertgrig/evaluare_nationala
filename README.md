# Evaluare Națională — Sibiu high school admissions

A SQLite database modeling Sibiu county's 9th-grade high school admission plan
("Plan de școlarizare clasa a IX-a"), real Evaluare Națională candidate data
for 2025 and 2026, and a deterministic seat-fill simulation that predicts
admission cutoff grades for the county's top 6 high schools.

## Contents

- **`schema.sql`** — database schema: `schools`, `tracks`, `profiles`,
  `domains`, `specializations`, `languages`, `admission_offerings`,
  `candidates`, `simulated_cutoffs`.
- **`build_db.py`** — reproducible build script. Rebuilds `admissions.db`
  from scratch: schools/offerings (transcribed from the official admission
  plan) plus both years of candidate data.
- **`candidates_2026.csv`** / **`candidates_2025.csv`** — real Evaluare
  Națională candidate results for Sibiu county (Jud=33), scraped/converted
  from evaluare.edu.ro's county ranking, one row per candidate. The `media`
  column is the final admission average, computed from each subject's *notă
  finală* (post-contestație grade), so the 2026 data reflects the resolved
  final ranking, not the initial pre-challenge grades.
- **`scrape_candidates_2026.py`** — re-scrapes the 2026 candidate list from
  evaluare.edu.ro's paginated `CandFromJudIAD.aspx` endpoint (mints an
  ASP.NET session, pages through the county ranking, retries the endpoint's
  intermittent 302s) and rewrites `candidates_2026.csv`.
- **`seed.sql`** — plain-SQL dump of the built database, for portability
  without running the build script.
- **`admissions.db`** — the built SQLite database.
- **`simulate_top6_model.py`** — the seat-fill simulation model for the top
  6 schools (see below).
- **`simulated_admissions_before_contestations.pdf`** /
  **`simulated_admissions_after_contestations.pdf`** — the projected-cutoff
  table rendered to PDF, from the candidate data before vs. after the 2026
  contestații were resolved.

## Setup

```bash
python3 build_db.py          # rebuilds admissions.db from the CSVs + schema.sql
python3 simulate_top6_model.py --year 2025   # run the simulation
python3 simulate_top6_model.py --year 2026
```

### Where would a given candidate land?

Pass `--target GRADE` to drop one hypothetical candidate into the pool and
report which class they'd be admitted to. Add `--german-native` if the
candidate is eligible for German native-language (German-medium) classes,
which unlocks the German-medium seats at Brukenthal and Ghibu. Add
`--exclude TERM` (repeatable) to make that candidate refuse any specialization
whose name contains `TERM` (case-insensitive).

```bash
# non-German-track candidate with an 8.67 average, against the 2026 pool
python3 simulate_top6_model.py --year 2026 --target 8.67
#   -> LT Onisifor Ghibu — Matematică-Informatică (intensiv Informatică)
#      seat 28 of 28, simulated cutoff 8.65

# German-native-eligible candidate with a lower 8.60 average
python3 simulate_top6_model.py --year 2026 --target 8.60 --german-native
#   -> LT Onisifor Ghibu — Științe ale naturii (German-medium)
#      seat 28 of 28, simulated cutoff 8.50

# same 8.60 candidate, but unwilling to do Filologie
python3 simulate_top6_model.py --year 2026 --target 8.60 --exclude Filologie
#   -> LT Constantin Noica — Științe ale naturii (intensiv engleză)
#      seat 28 of 28, simulated cutoff 8.50
```

The examples show why eligibility and preferences matter: the German-native
candidate gets in at a *lower* grade because German-medium seats are open only
to them, and excluding a specialization can push a candidate down a rung (or
out of the top 6 entirely if it was their only foothold). Note that `--target`
re-persists that run's cutoffs (with the extra candidate included) to the
`simulated_cutoffs` table; re-run without `--target` to restore the clean
projection.

## The simulation model

`simulate_top6_model.py` predicts each class's admission cutoff grade by
greedily assigning candidates (best grade first) to their highest-priority
available seat, for the 6 highest-ranked Sibiu high schools: Gheorghe Lazăr,
Octavian Goga, Samuel von Brukenthal, Onisifor Ghibu, Constantin Noica, and
Liceul Teologic Baptist Betania.

It's validated against real 2025 outcomes (mean absolute error 0.058,
max 0.20 across 25 classes with known prior-year cutoffs) and includes
several empirically-derived rules layered on top of a plain deterministic
ranking — school/track prestige ordering, German-medium and vocational
eligibility rules, and a couple of flat corrections for demand that leaks
to schools outside this dataset (music, theology, architecture, etc.). See
the module docstring in `simulate_top6_model.py` for the full rule list and
the reasoning/validation numbers behind each one.

Results are persisted to the `simulated_cutoffs` table, keyed by
`candidate_pool_year` and `model_version`, alongside the actual recorded
cutoff for comparison.
