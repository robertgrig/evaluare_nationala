-- High school admissions database
-- Models the Romanian "Plan de scolarizare clasa a IX-a" admission sheet:
-- for each high school, the class offerings available at IXth grade, split by
-- track/profile/domain/specialization, teaching language (incl. bilingual),
-- DUAL (work-study) form, and seat breakdown, with last year's cutoff grade.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS simulated_cutoffs;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS admission_offerings;
DROP TABLE IF EXISTS specializations;
DROP TABLE IF EXISTS domains;
DROP TABLE IF EXISTS languages;
DROP TABLE IF EXISTS profiles;
DROP TABLE IF EXISTS tracks;
DROP TABLE IF EXISTS schools;

CREATE TABLE schools (
    id               INTEGER PRIMARY KEY,
    sheet_row_no     INTEGER,           -- "Nr. crt" of the school block on the source sheet
    name             TEXT NOT NULL,
    address          TEXT,
    phone            TEXT,
    email            TEXT,
    rating           REAL,              -- external rating, not on the sheet; fill in separately
    parent_school_id INTEGER REFERENCES schools(id), -- set when this school is a "structura" hosted at another school
    grade_rank       INTEGER            -- 1 = best; ranked by this school's highest last_admission_grade (ties share a rank)
);

-- Filiera: Teoretica, Vocationala, Tehnologica
CREATE TABLE tracks (
    id   INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Profil: Real, Umanist, Artistic, Pedagogic, Teologic, ...
CREATE TABLE profiles (
    id   INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Domeniu de baza: middle tier used for vocational/artistic/theological
-- profiles (e.g. profile Artistic -> domain "Muzica" or "Arte Vizuale").
-- Left unused (no rows) for profiles where the sheet doesn't fill this column.
CREATE TABLE domains (
    id         INTEGER PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    name       TEXT NOT NULL,
    UNIQUE(profile_id, name)
);

-- Specializare/Calificare nivel 4, scoped to a profile and (optionally) a domain.
CREATE TABLE specializations (
    id         INTEGER PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES profiles(id),
    domain_id  INTEGER REFERENCES domains(id),
    name       TEXT NOT NULL,       -- Specializare/Calificare nivel 4
    UNIQUE(profile_id, domain_id, name)
);

-- Limba de predare / Bilingv values: Romana, Engleza, Franceza, Germana,
-- Maghiara, ...
CREATE TABLE languages (
    id   INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- One row per class offering as it appears on the admission sheet.
CREATE TABLE admission_offerings (
    id                    INTEGER PRIMARY KEY,
    school_id             INTEGER NOT NULL REFERENCES schools(id),
    track_id              INTEGER NOT NULL REFERENCES tracks(id),
    profile_id            INTEGER NOT NULL REFERENCES profiles(id),
    specialization_id     INTEGER NOT NULL REFERENCES specializations(id),
    language_id           INTEGER NOT NULL REFERENCES languages(id),   -- Limba de predare
    bilingual_language_id INTEGER REFERENCES languages(id),            -- Bilingv (secondary language), nullable
    is_dual               INTEGER NOT NULL DEFAULT 0,                  -- Forma de organizare (inv. DUAL): Da=1/Nu=0
    qualification_code    TEXT,                                        -- Cod specializare/calificare
    qualification_level3  TEXT,       -- Calificare nivel 3 (varies per offering, not per specialization)
    school_year           TEXT NOT NULL,                               -- e.g. '2026-2027'
    num_classes           REAL,       -- Nr. clase a IX-a (can be fractional, e.g. 0.5)
    num_places            INTEGER,    -- Nr. locuri
    num_roma_places       INTEGER,    -- Nr. locuri speciale romi
    num_ces_places        INTEGER,    -- Nr. locuri speciale CES
    last_admission_grade  REAL,       -- Ultima medie de admitere (prior year cutoff); NULL when new/unreadable
    is_new_program         INTEGER NOT NULL DEFAULT 0,  -- sheet says "nou" (no prior-year cutoff exists yet)
    notes                  TEXT,      -- freeform annotations spotted on the sheet (e.g. handwritten marks)
    UNIQUE(school_id, track_id, specialization_id, language_id, school_year, qualification_code)
);

CREATE INDEX idx_offerings_school        ON admission_offerings(school_id);
CREATE INDEX idx_offerings_language      ON admission_offerings(language_id);
CREATE INDEX idx_offerings_profile       ON admission_offerings(profile_id);
CREATE INDEX idx_offerings_code          ON admission_offerings(qualification_code);
CREATE INDEX idx_specializations_profile ON specializations(profile_id);
CREATE INDEX idx_domains_profile         ON domains(profile_id);

-- Evaluare Nationala candidates: the IXth-grade applicant pool whose scores
-- determine admission against the schools/admission_offerings cutoffs above.
-- Source: evaluare.edu.ro county ranking (Jud=33), full county leaderboard —
-- one row per candidate (anonymized code). grade_matematica/grade_average
-- are NULL when the candidate was marked "Absent" for that exam.
CREATE TABLE candidates (
    id                     INTEGER PRIMARY KEY,
    year                   INTEGER NOT NULL,  -- exam year, e.g. 2026 (plain int, for easy cross-year filtering)
    nr                     INTEGER,           -- NR column (row number on the source sheet)
    idx                    INTEGER,           -- Index column
    candidate_code         TEXT NOT NULL,     -- Codul candidatului, e.g. 'SB10121803' (unique per year, not globally)
    national_rank          INTEGER,           -- Pozitia in ierarhia Evaluare Nationala
    source_school          TEXT,              -- Scoala de provenienta (gimnaziu, not a high school)
    grade_romana           REAL,              -- Limba si literatura romana
    grade_matematica       REAL,              -- Matematica
    native_language        TEXT,              -- Limba si literatura materna: limba (e.g. 'Limba germana')
    grade_native_language  REAL,              -- Limba si literatura materna: nota
    grade_average          REAL,              -- Media la evaluarea nationala
    school_year            TEXT NOT NULL,     -- admissions cycle this evaluation feeds, e.g. '2026-2027'
    UNIQUE(candidate_code, year)
);

CREATE INDEX idx_candidates_rank ON candidates(national_rank);
CREATE INDEX idx_candidates_avg  ON candidates(grade_average);
CREATE INDEX idx_candidates_year ON candidates(year);

-- Output of the top-6-schools seat-fill simulation (see simulate_top6_model.py).
-- One row per admission_offerings row covered by the simulation, storing the
-- validated "final model" configuration's projected cutoff alongside the
-- actual recorded cutoff for comparison. Re-running the script replaces all
-- rows for that model_version + candidate_pool_year.
CREATE TABLE simulated_cutoffs (
    id                   INTEGER PRIMARY KEY,
    offering_id          INTEGER NOT NULL REFERENCES admission_offerings(id),
    candidate_pool_year  INTEGER NOT NULL,  -- which year's candidates were run through the model, e.g. 2025
    model_version        TEXT NOT NULL,     -- identifies the model configuration, e.g. 'top6_v1'
    simulated_cutoff      REAL,             -- grade of the last candidate assigned to this seat (NULL if unfilled)
    actual_cutoff         REAL,             -- last_admission_grade at the time of this run, for convenience
    run_at                TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(offering_id, candidate_pool_year, model_version)
);

CREATE INDEX idx_simulated_cutoffs_offering ON simulated_cutoffs(offering_id);
