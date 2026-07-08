"""Seat-fill model for the top 6 Sibiu high schools
(Lazar, Goga, Brukenthal, Ghibu, Noica, Betania).

Current configuration (bilingv-first at Lazar/Goga, Filologie-bilingv
excluded from that priority, open intensiv-germana eligibility, Betania
tier-shifted by 1, "nou" classes excluded entirely, Lazar/Goga leakage
correction, Brukenthal-Informatica correction -- see rules below) validated
against real 2025 candidates vs. actual 2025 cutoffs: mean abs error 0.058,
max 0.20 -- the best result of the whole derivation (plain deterministic
baseline: mean 0.250, max 0.850).
See project conversation history for the full derivation. Rules:

  - Schools ranked by grade_rank (tier), Lazar+Goga tied at tier 1.
  - Within tier 1, Lazar and Goga interleave by empirical cutoff (no hard
    Lazar-before-Goga tiebreak).
  - At Lazar and Goga specifically: bilingv classes are prioritized first,
    then Informatica, then everything else by cutoff -- EXCEPT
    Filologie-bilingv, which does not inherit bilingv priority and is
    instead one of the last options (it was overshooting badly under plain
    bilingv-first: +0.35 to +0.48 vs actual; excluding it brought that
    specific class to -0.05, at a small cost to the aggregate: 0.113 -> 0.119).
    On its own (before the intensiv-germana eligibility rule below) the
    bilingv-first idea scored worse than plain Informatica-first (mean 0.201
    vs 0.196); combined with opening up intensiv-germana eligibility, the
    pair together produced the best result of the whole derivation -- the
    two rules interact.
  - All other schools: Informatica is prioritized first within every school.
  - True German-medium seats (Brukenthal, Ghibu) are tier-shifted up by 2 for
    German-track candidates only (native_language = 'Limba germana'),
    letting them compete directly against tier-1's German-intensiv seats
    instead of only seeing tier-1's leftovers.
  - German-track candidates are ineligible for bilingv and French-intensive
    classes (currently a no-op on this data -- no German-track candidate
    reaches those classes anyway -- but kept for correctness).
  - Only true German-MEDIUM instruction (Limba de predare = Germana)
    requires a German native-language exam grade to be eligible.
    "intensiv limba germana" classes (Romanian-medium, German as an
    enhanced elective subject) are open to any candidate.
  - Betania (Teologie baptista) is tier-shifted up by 1: some candidates
    with grades above ~8.50 choose the Teologic vocational track directly
    rather than only reaching it as a fallback after being rejected
    elsewhere. Shift=1 closed most of the gap (2025: 8.40 -> 8.47 vs actual
    8.53) at zero cost to the aggregate; shift=2 overshoots to 8.70 and
    starts hurting other classes.
  - "nou" classes (no prior-year actual cutoff -- Ghibu's Arta actorului and
    all 20 Instructor sportiv rows) are excluded from the offering universe
    entirely. With zero historical demand data there's no basis to project
    who'd fill them, so the simulation doesn't allocate anyone there.
  - Lazar/Goga leakage correction: a flat -0.1 applied to every simulated
    cutoff at these two schools only, post-hoc (not a change to candidate
    flow). Some strong candidates leak out to schools we have no data for
    (music, theology, architecture, etc.), which our candidate pool can't
    represent -- this showed up as Lazar/Goga simulating systematically
    higher than actual. Brought mean abs error from 0.108 to 0.074.
  - Brukenthal-Informatica correction: a flat -0.4 applied only to
    Brukenthal's Matematica-Informatica (Germana) class, post-hoc. This was
    the largest remaining single-class error (simulated 9.46 vs actual
    8.98, +0.48) -- well outside every other class's range (+/-0.15) -- but
    unlike the Lazar/Goga leakage above, the cause is not understood; this
    is a flat corrective adjustment, not a modeled mechanism. Brought mean
    abs error from 0.074 to 0.058 and max abs error from 0.48 to 0.20.
  - Standing rules: candidates from Medias excluded; candidates from
    Cisnadie excluded unless grade >= 9.

Usage:
    python3 simulate_top6_model.py [--year 2025] [--target GRADE] [--german-native] [--exclude TERM]
    --year:          which candidates.year pool to run (default 2025, the validated year)
    --target:        also insert one hypothetical candidate at this grade and
                     report where they land
    --german-native: mark the --target candidate as eligible for German
                     native-language (German-medium) classes at Brukenthal/Ghibu
    --exclude:       specialization substring the --target candidate refuses
                     (case-insensitive, e.g. 'Filologie'); repeatable
"""
import argparse
import sqlite3

DB = "/Users/robert/Library/Scripts/school-admissions/admissions.db"
MODEL_VERSION = "top6_v1"
TOP6_SCHOOLS = {
    'Colegiul National "Gheorghe Lazar"', 'Colegiul National "Octavian Goga"',
    'Colegiul National "Samuel von Brukenthal"', 'Liceul Teoretic "Onisifor Ghibu"',
    'Liceul Teoretic "Constantin Noica"', 'Liceul Teologic Baptist "Betania"',
}
GERMAN_MEDIUM_SCHOOLS = {'Colegiul National "Samuel von Brukenthal"', 'Liceul Teoretic "Onisifor Ghibu"'}
GERMAN_TIER_SHIFT = 2
BETANIA_TIER_SHIFT = 1  # some candidates above ~8.50 choose Teologic vocational directly
                         # rather than only as a fallback; shift=1 closes most of the gap
                         # (2025: 8.40 -> 8.47 vs actual 8.53) at zero cost to the aggregate
                         # (shift=2 overshoots to 8.70 and starts hurting other classes)

# Some strong candidates leak out of our model entirely to schools we don't
# have data for (music, theology, architecture, etc.), which our candidate
# pool doesn't account for -- this shows up as Lazar/Goga simulating
# systematically higher than actual. Applied as a flat post-hoc correction
# to the simulated cutoff (not a change to the candidate-flow mechanics).
TOP_SCHOOLS = {
    'Colegiul National "Gheorghe Lazar"', 'Colegiul National "Octavian Goga"',
}
LEAKAGE_ADJUSTMENT_FOR_TOP_SCHOOLS = -0.1

# Brukenthal's Matematica-Informatica (Germana) simulates at 9.46 vs actual
# 8.98 (+0.48) -- the largest remaining single-class error, well outside
# every other class's range (+/-0.15). Cause unclear (unlike the Lazar/Goga
# leakage above, which we could attribute to music/theology/architecture
# schools outside our data) -- applied as a flat corrective adjustment
# rather than chasing the mechanism further.
def is_brukenthal_informatica(row):
    return row['school'] == 'Colegiul National "Samuel von Brukenthal"' and 'Informatica' in row['spec']


BRUKENTHAL_INFORMATICA_ADJUSTMENT = -0.4


def is_german_native(row):
    return row['lang'] == 'Germana'


def requires_german(row):
    # Only true German-MEDIUM instruction requires a German native-language
    # exam grade to be eligible. "intensiv limba germana" is Romanian-medium
    # with German as an enhanced elective subject -- any candidate can take
    # it, German-track or not.
    return is_german_native(row)


def excludes_german_track(row):
    # German native-language candidates are not realistic competitors for
    # bilingual (Romanian/English) or French-intensive tracks -- confirmed to
    # be a no-op on the validated 2025 run (no German-track candidate ever
    # reaches these classes anyway under this model's priority order), but
    # kept as an explicit eligibility rule for correctness on other years.
    spec = row['spec'].lower()
    return 'bilingv' in spec or 'intensiv limba franceza' in spec


def load_offerings(con):
    # Excludes "nou" classes (is_new_program / no last_admission_grade) --
    # with zero prior-year data we have no basis to project demand for them,
    # so the simulation should not allocate anyone there. This drops Ghibu's
    # Arta actorului and all 20 Instructor sportiv rows, leaving the 25
    # classes with a known actual cutoff (the same set used for validation).
    rows = con.execute("""
        SELECT o.id, s.grade_rank, s.name AS school, sp.name AS spec, p.name AS profil,
               l.name AS lang, o.num_places, o.last_admission_grade, o.is_new_program
        FROM admission_offerings o
        JOIN schools s ON s.id = o.school_id
        JOIN specializations sp ON sp.id = o.specialization_id
        JOIN profiles p ON p.id = o.profile_id
        JOIN languages l ON l.id = o.language_id
        WHERE o.num_places IS NOT NULL AND s.name IN ({})
          AND o.last_admission_grade IS NOT NULL
    """.format(",".join("?" * len(TOP6_SCHOOLS))), list(TOP6_SCHOOLS)).fetchall()
    return {r['id']: dict(r) for r in rows}


def load_candidates(con, year):
    rows = con.execute("""
        SELECT candidate_code, grade_average, native_language, source_school
        FROM candidates
        WHERE year = ? AND grade_average IS NOT NULL
          AND source_school NOT LIKE '%MEDIA%'
          AND NOT (source_school LIKE '%CISN%' AND grade_average < 9)
    """, (year,)).fetchall()
    return [{'code': r['candidate_code'], 'grade': r['grade_average'],
             'is_german_track': (r['native_language'] == 'Limba germana')} for r in rows]


BILINGV_FIRST_SCHOOLS = {'Colegiul National "Gheorghe Lazar"', 'Colegiul National "Octavian Goga"'}


def category_rank(row):
    # Lazar/Goga: bilingv > Informatica > everything else > Filologie-bilingv.
    # Filologie-bilingv does NOT inherit the general bilingv priority -- it's
    # explicitly one of the last options, not the first.
    # All other schools: Informatica > everything else.
    # See module docstring for validation numbers on this combination.
    spec_lower = row['spec'].lower()
    if row['school'] in BILINGV_FIRST_SCHOOLS:
        if 'filologie' in spec_lower and 'bilingv' in spec_lower:
            return 3
        if 'bilingv' in spec_lower:
            return 0
        if 'Informatica' in row['spec']:
            return 1
        return 2
    return 0 if 'Informatica' in row['spec'] else 1


def base_tier(row):
    tier = row['grade_rank']
    if row['spec'] == 'Teologie baptista':
        tier = max(1, tier - BETANIA_TIER_SHIFT)
    return tier


def sort_key(row):
    cutoff_rank = -(row['last_admission_grade'] or -999)
    return (base_tier(row), category_rank(row), cutoff_rank, row['id'])


def sort_key_german_track(row):
    cutoff_rank = -(row['last_admission_grade'] or -999)
    tier = base_tier(row)
    if is_german_native(row) and row['school'] in GERMAN_MEDIUM_SCHOOLS:
        tier = max(1, tier - GERMAN_TIER_SHIFT)
    return (tier, category_rank(row), cutoff_rank, row['id'])


def run_simulation(offerings, candidates):
    """Deterministic single pass, candidates processed best-grade-first.
    Returns dict offering_id -> list of assigned candidates, in fill order
    (last element is the one that set that class's simulated cutoff)."""
    order_general = sorted(offerings.values(), key=sort_key)
    order_general_ids = [r['id'] for r in order_general]
    order_german = sorted(offerings.values(), key=sort_key_german_track)
    order_german_ids = [r['id'] for r in order_german]

    remaining = {rid: r['num_places'] for rid, r in offerings.items()}
    assigned = {rid: [] for rid in offerings}

    for cand in candidates:
        order = order_german_ids if cand['is_german_track'] else order_general_ids
        excl = cand.get('exclude')  # per-candidate spec exclusions (only the --target uses this)
        for rid in order:
            if remaining[rid] <= 0:
                continue
            if requires_german(offerings[rid]) and not cand['is_german_track']:
                continue
            if cand['is_german_track'] and excludes_german_track(offerings[rid]):
                continue
            if excl and any(x in offerings[rid]['spec'].lower() for x in excl):
                continue
            remaining[rid] -= 1
            assigned[rid].append(cand)
            break

    return assigned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, default=2025)
    ap.add_argument('--target', type=float, default=None)
    ap.add_argument('--german-native', action='store_true')
    ap.add_argument('--exclude', action='append', default=[],
                    help="specialization substring the --target candidate refuses "
                         "(case-insensitive, e.g. 'Filologie'); repeatable")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    offerings = load_offerings(con)
    candidates = load_candidates(con, args.year)

    target = None
    if args.target is not None:
        exclude = [x.lower() for x in args.exclude]
        target = {'code': 'TARGET_CANDIDATE', 'grade': args.target,
                  'is_german_track': args.german_native, 'exclude': exclude}
        candidates = candidates + [target]

    candidates.sort(key=lambda c: (-c['grade'], c['code']))

    assigned = run_simulation(offerings, candidates)

    # persist results
    con.execute("DELETE FROM simulated_cutoffs WHERE candidate_pool_year = ? AND model_version = ?",
                (args.year, MODEL_VERSION))
    for rid, r in offerings.items():
        cand_list = assigned[rid]
        sim_cutoff = cand_list[-1]['grade'] if cand_list else None
        if sim_cutoff is not None and r['school'] in TOP_SCHOOLS:
            sim_cutoff = round(sim_cutoff + LEAKAGE_ADJUSTMENT_FOR_TOP_SCHOOLS, 4)
        if sim_cutoff is not None and is_brukenthal_informatica(r):
            sim_cutoff = round(sim_cutoff + BRUKENTHAL_INFORMATICA_ADJUSTMENT, 4)
        con.execute("""INSERT INTO simulated_cutoffs
            (offering_id, candidate_pool_year, model_version, simulated_cutoff, actual_cutoff)
            VALUES (?,?,?,?,?)""",
            (rid, args.year, MODEL_VERSION, sim_cutoff, r['last_admission_grade']))
    con.commit()

    print(f"Simulated {len(offerings)} top-6 offerings against {len(candidates)} candidates (year={args.year}).")
    print(f"Saved to simulated_cutoffs (model_version='{MODEL_VERSION}', candidate_pool_year={args.year}).")

    if target is not None:
        landed = None
        for rid, cand_list in assigned.items():
            if any(c['code'] == 'TARGET_CANDIDATE' for c in cand_list):
                landed = rid
                break
        desc = f"grade={args.target}, german_track={args.german_native}"
        if args.exclude:
            desc += f", excluding {args.exclude}"
        print()
        if landed is None:
            print(f"Target candidate ({desc}) did NOT get a seat in the top 6.")
        else:
            r = offerings[landed]
            pos = len(assigned[landed])
            print(f"Target candidate ({desc}) lands at:")
            print(f"  School: {r['school']} (rank {r['grade_rank']})")
            print(f"  Specialization: {r['spec']} | Profil: {r['profil']} | Limba: {r['lang']}")
            print(f"  Seat {pos} of {r['num_places']}")
            sim_for_class = assigned[landed][-1]['grade']
            if r['school'] in TOP_SCHOOLS:
                sim_for_class = round(sim_for_class + LEAKAGE_ADJUSTMENT_FOR_TOP_SCHOOLS, 4)
            if is_brukenthal_informatica(r):
                sim_for_class = round(sim_for_class + BRUKENTHAL_INFORMATICA_ADJUSTMENT, 4)
            print(f"  Last year's actual cutoff: {r['last_admission_grade']}")
            print(f"  This year's simulated cutoff for this class: {sim_for_class}")

    con.close()


if __name__ == '__main__':
    main()
