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
  from evaluare.edu.ro's county ranking, one row per candidate.
- **`seed.sql`** — plain-SQL dump of the built database, for portability
  without running the build script.
- **`admissions.db`** — the built SQLite database.
- **`simulate_top6_model.py`** — the seat-fill simulation model for the top
  6 schools (see below).

## Setup

```bash
python3 build_db.py          # rebuilds admissions.db from the CSVs + schema.sql
python3 simulate_top6_model.py --year 2025   # run the simulation
python3 simulate_top6_model.py --year 2026
```

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
