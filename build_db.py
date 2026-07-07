import sqlite3, os, csv

DB = "/Users/robert/Library/Scripts/school-admissions/admissions.db"
SCHEMA = "/Users/robert/Library/Scripts/school-admissions/schema.sql"
CANDIDATES_CSV = "/Users/robert/Library/Scripts/school-admissions/candidates_2026.csv"
YEAR = "2026-2027"
CANDIDATES_YEAR = 2026
CANDIDATES_2025_CSV = "/Users/robert/Library/Scripts/school-admissions/candidates_2025.csv"
YEAR_2025 = "2025-2026"
CANDIDATES_YEAR_2025 = 2025

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open(SCHEMA).read())
cur = con.cursor()

def get_or_create(table, unique_cols, row):
    where = " AND ".join(f"{c} IS ?" for c in unique_cols)
    cur.execute(f"SELECT id FROM {table} WHERE {where}", [row[c] for c in unique_cols])
    r = cur.fetchone()
    if r:
        return r[0]
    cols = list(row.keys())
    cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                [row[c] for c in cols])
    return cur.lastrowid

def track(name): return get_or_create("tracks", ["name"], {"name": name})
def profile(name): return get_or_create("profiles", ["name"], {"name": name})
def domain(profile_id, name): return get_or_create("domains", ["profile_id", "name"], {"profile_id": profile_id, "name": name})
def spec(profile_id, domain_id, name): return get_or_create("specializations", ["profile_id", "domain_id", "name"], {"profile_id": profile_id, "domain_id": domain_id, "name": name})
def lang(name): return get_or_create("languages", ["name"], {"name": name})

def school(sheet_row_no, name, address, phone, email, parent_id=None):
    return get_or_create("schools", ["name"], {
        "sheet_row_no": sheet_row_no, "name": name, "address": address,
        "phone": phone, "email": email, "rating": None, "parent_school_id": parent_id,
    })

def offering(school_id, track_name, profile_name, domain_name, spec_name, lang_name,
             bilingv_name=None, level3=None, is_dual=False, code=None,
             clase=None, locuri=None, romi=None, ces=None, medie=None, notes=None):
    t = track(track_name)
    p = profile(profile_name)
    d = domain(p, domain_name) if domain_name else None
    s = spec(p, d, spec_name)
    l = lang(lang_name)
    bl = lang(bilingv_name) if bilingv_name else None
    is_new = 1 if medie == "nou" else 0
    grade = None if (medie is None or medie == "nou") else float(medie)
    cur.execute("""INSERT INTO admission_offerings
        (school_id, track_id, profile_id, specialization_id, language_id, bilingual_language_id,
         is_dual, qualification_code, qualification_level3, school_year, num_classes, num_places,
         num_roma_places, num_ces_places, last_admission_grade, is_new_program, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (school_id, t, p, s, l, bl, 1 if is_dual else 0, code, level3, YEAR, clase, locuri,
         romi, ces, grade, is_new, notes))

# ---------------------------------------------------------------- schools --
lazar     = school(1, 'Colegiul National "Gheorghe Lazar"', 'Str. Lazar Gheorghe 1, Sibiu', '0269212896', 'cnglazar@gmail.com')
goga      = school(2, 'Colegiul National "Octavian Goga"', 'Str. Mitropoliei/Bastionului 34/7, Sibiu', '0269210082', 'secretariat@cnogsibiu.ro')
brukenthal= school(3, 'Colegiul National "Samuel von Brukenthal"', 'Piata Huet 5, Sibiu', '0269211322', 'office@brukenthal.ro')
saguna    = school(4, 'Colegiul National Pedagogic "Andrei Saguna"', 'Str. Turnu Rosu 2, Sibiu', '0269434002', 'cnpas_sb@yahoo.com')
arta      = school(5, 'Liceul de Arta Sibiu', 'Str. Alexandru Odobescu 2, Sibiu', '0269211458', 'office@licartsibiu.ro')
noica     = school(6, 'Liceul Teoretic "Constantin Noica"', 'Str. Ostirii 5, Sibiu', '0269233790', 'lcnoica@yahoo.com')
betania   = school(6, 'Liceul Teologic Baptist "Betania"', 'Str. Nicolae Iorga nr. 56B, Sibiu', '0269233790', 'contact@liceulbetania.ro', parent_id=noica)
ghibu     = school(7, 'Liceul Teoretic "Onisifor Ghibu"', 'Str. Bihorului 3, Sibiu', '0269224882', 'office@onisifor-ghibu.ro')
energetic = school(8, 'Colegiul Tehnic Energetic Sibiu', 'Str. Electricienilor 1, Sibiu', '0269244351', 'colegiulenergetic@gmail.com')
barcianu  = school(9, 'Colegiul Agricol "Daniil Popovici Barcianu"', 'Str. Banatului 2, Sibiu', '0269211368', 'barcianu@yahoo.com')
baritiu   = school(10, 'Colegiul Economic "George Baritiu"', 'Str. Oituz 31, Sibiu', '0269424238', 'liceuleconomic@yahoo.com')
cibinium  = school(11, 'Colegiul Tehnic "Cibinium"', 'Str. Dealului 4, Sibiu', '0269211547', 'colegiulcibinium@yahoo.com')
henri     = school(11, 'Liceul Tehnologic "Henri Coanda"', 'Str. Henri Coanda nr. 51, Sibiu', '0269238313', 'gsicmsibiu@yahoo.com', parent_id=cibinium)
avramiancu= school(12, 'Liceul Tehnologic "Avram Iancu"', 'Str. Movilei 8, Sibiu', '0269210925', 'grlemn@yahoo.com')
independenta = school(13, 'Liceul Tehnologic "Independenta"', 'Str. Gladiolelor 2, Sibiu', '0269221806', 'independenta_77@yahoo.com')
terezianum   = school(14, 'Liceul Tehnologic de Industrie Alimentara "Terezianum"', 'Str. Postavarilor 18, Sibiu', '0269218797', 'colegiulalimentarsibiu@yahoo.com')

# ------------------------------------------------------------- offerings --

# 1. Gheorghe Lazar
offering(lazar,'Teoretica','Real',None,'Matematica-Informatica - intensiv Informatica','Romana', code='103', clase=1, locuri=28, romi=1, ces=1, medie=9.37)
offering(lazar,'Teoretica','Real',None,'Stiinte ale naturii - intensiv limba franceza','Romana', code='104', clase=1, locuri=28, romi=1, ces=1, medie=9.05)
offering(lazar,'Teoretica','Real',None,'Stiinte ale naturii - intensiv limba germana','Romana', code='104', clase=1, locuri=28, romi=1, ces=1, medie=9.05)
offering(lazar,'Teoretica','Real',None,'Stiinte ale naturii','Romana', code='104', clase=1, locuri=28, romi=1, ces=1, medie=9.05)
offering(lazar,'Teoretica','Real',None,'Stiinte ale naturii - bilingv','Romana', bilingv_name='Engleza', code='105', clase=2, locuri=56, romi=2, ces=2, medie=9.42)

# 2. Octavian Goga
offering(goga,'Teoretica','Real',None,'Matematica-Informatica - intensiv Informatica','Romana', code='106', clase=1, locuri=28, romi=1, ces=1, medie=9.22)
offering(goga,'Teoretica','Real',None,'Stiinte ale naturii','Maghiara', code='107', clase=1, locuri=28, romi=1, ces=1, medie=9.12,
         notes='Sheet has a handwritten wavy line struck through this row (Limba maghiara) — verify with school if still offered.')
offering(goga,'Teoretica','Real',None,'Stiinte ale naturii - intensiv limba germana','Romana', code='108', clase=1, locuri=28, romi=1, ces=1, medie=9.12)
offering(goga,'Teoretica','Real',None,'Stiinte ale naturii - bilingv','Romana', bilingv_name='Engleza', code='109', clase=1, locuri=28, romi=1, ces=1, medie=9.42)
offering(goga,'Teoretica','Umanist',None,'Filologie - intensiv limba engleza','Romana', code='110', clase=1, locuri=28, romi=1, ces=1, medie=8.87)
offering(goga,'Teoretica','Umanist',None,'Filologie - bilingv','Romana', bilingv_name='Engleza', code='111', clase=1, locuri=28, romi=1, ces=1, medie=8.97)
offering(goga,'Teoretica','Umanist',None,'Stiinte sociale','Romana', code='112', clase=2, locuri=56, romi=2, ces=2, medie=8.92)

# 3. Samuel von Brukenthal
offering(brukenthal,'Teoretica','Real',None,'Matematica-Informatica - intensiv Informatica','Germana', code='113', clase=1, locuri=28, romi=1, ces=1, medie=8.98)
offering(brukenthal,'Teoretica','Real',None,'Stiinte ale naturii','Germana', code='114', clase=2, locuri=56, romi=2, ces=2, medie=8.98)
offering(brukenthal,'Teoretica','Umanist',None,'Filologie','Germana', code='115', clase=1, locuri=28, romi=1, ces=1, medie=8.75)

# 4. Andrei Saguna
offering(saguna,'Vocationala','Pedagogic',None,'Pedagogia educatiei timpurii','Romana', code='1000', clase=1, locuri=24, romi=1, ces=1, medie=8.15)
offering(saguna,'Vocationala','Pedagogic',None,'Pedagogia invatamantului primar','Germana', code='1001', clase=1, locuri=24, romi=1, ces=1, medie=7.88)
offering(saguna,'Vocationala','Pedagogic',None,'Pedagogia invatamantului primar','Romana', code='1002', clase=2, locuri=48, romi=2, ces=2, medie=8.45)
offering(saguna,'Teoretica','Umanist',None,'Filologie','Germana', code='116', clase=1, locuri=28, romi=1, ces=1, medie=7.61)
offering(saguna,'Teoretica','Umanist',None,'Filologie - bilingv','Romana', bilingv_name='Engleza', code='117', clase=1, locuri=28, romi=1, ces=1, medie=8.4)

# 5. Liceul de Arta
offering(arta,'Vocationala','Artistic','Arte Vizuale','Arte Vizuale','Romana', code='1003', clase=1, locuri=24, romi=1, ces=1, medie=7.23)
offering(arta,'Vocationala','Artistic','Muzica','Interpretare instrumentala','Romana', code='1004', clase=0.5, locuri=13, romi=None, ces=1, medie=6.4)
offering(arta,'Vocationala','Artistic','Muzica','Interpretare vocala','Romana', code='1005', clase=0.5, locuri=11, romi=1, ces=None, medie=6.4)

# 6. Constantin Noica
offering(noica,'Teoretica','Real',None,'Stiinte ale naturii - intensiv limba engleza','Romana', code='126', clase=1, locuri=28, romi=1, ces=1, medie=8.65)
offering(noica,'Teoretica','Real',None,'Stiinte ale naturii','Romana', code='126', clase=1, locuri=28, romi=1, ces=1, medie=8.65)
offering(noica,'Teoretica','Umanist',None,'Filologie','Romana', code='127', clase=1, locuri=28, romi=1, ces=1, medie=8.5)
offering(noica,'Teoretica','Umanist',None,'Filologie - intensiv limba engleza','Romana', code='127', clase=1, locuri=28, romi=1, ces=1, medie=8.5)

# Betania (structura la Noica)
offering(betania,'Vocationala','Teologic','Teologic','Teologie baptista','Romana', code='1009', clase=1, locuri=24, romi=1, ces=1, medie=8.53)

# 7. Onisifor Ghibu
offering(ghibu,'Vocationala','Artistic','Arta actorului','Arta actorului','Romana', code='1022', clase=1, locuri=24, romi=1, ces=1, medie='nou')

_sport_note = 'Sheet shows Nr.locuri speciale romi=1 / CES=1 / Ultima medie=nou as ONE merged cell spanning all 20 "Instructor sportiv" rows in this domain, not per row — treat as a shared pool for the whole Sportiv domain at this school, not per specialization.'
_sport_events = [
    ('Baschet', '1023', 2), ('Box', '1024', 1), ('Calarie', '1025', 1),
    ('Dansuri populare', '1026', 1), ('Fotbal', '1027', 4),
    ('Gimnastica artistica sportiva', '1028', 1), ('Handbal', '1029', 1),
    ('Judo', '1030', 1), ('Karate', '1031', 1), ('Orientare sportiva', '1032', 1),
    ('Patinaj viteza', '1033', 1), ('Rugby', '1034', 1), ('Schi alpin', '1035', 1),
    ('Sarituri in apa', '1036', 1), ('Taekwondo WTF', '1037', 1),
    ('Tenis de camp', '1038', 1), ('Tenis de masa', '1039', 1), ('Volei', '1040', 1),
    ('Inot', '1041', 1), ('Sah', '1042', 1),
]
for event, code, locuri in _sport_events:
    offering(ghibu,'Vocationala','Sportiv','Sportiv', f'Instructor sportiv - {event}', 'Romana',
             code=code, clase=0.05, locuri=locuri, romi=None, ces=None, medie='nou', notes=_sport_note)

offering(ghibu,'Teoretica','Real',None,'Matematica-Informatica - intensiv Informatica','Romana', code='130', clase=1, locuri=28, romi=1, ces=1, medie=8.92)
offering(ghibu,'Teoretica','Real',None,'Stiinte ale naturii','Germana', code='131', clase=1, locuri=28, romi=1, ces=1, medie=8.51)
offering(ghibu,'Teoretica','Real',None,'Stiinte ale naturii','Romana', code='132', clase=1, locuri=28, romi=1, ces=1, medie=8.9)
offering(ghibu,'Teoretica','Umanist',None,'Filologie - intensiv limba engleza','Germana', code='133', clase=1, locuri=28, romi=1, ces=1, medie=8.2)
offering(ghibu,'Teoretica','Umanist',None,'Filologie - intensiv limba engleza','Romana', code='134', clase=1, locuri=28, romi=1, ces=1, medie=8.75)

# 8. Colegiul Tehnic Energetic
offering(energetic,'Teoretica','Real',None,'Matematica-Informatica - intensiv Informatica','Romana', code='118', clase=1, locuri=28, romi=1, ces=1, medie=8.27)
offering(energetic,'Tehnologica','Tehnic','Electric','Tehnician electrotehnist','Romana', level3='Electrician exploatare joasa tensiune', code='413', clase=1, locuri=28, romi=1, ces=1, medie=7.77)
offering(energetic,'Tehnologica','Tehnic','Electric','Tehnician energetician','Romana', level3='Electrician sisteme fotovoltaice', code='414', clase=1, locuri=28, romi=1, ces=1, medie=7.77)
offering(energetic,'Tehnologica','Tehnic','Electromecanica','Tehnician electromecanic - intensiv limba engleza','Romana', level3='Electromecanic utilaje si instalatii industriale', code='415', clase=1, locuri=28, romi=1, ces=1, medie=7.9)
offering(energetic,'Tehnologica','Tehnic','Electronica automatizari','Tehnician electronist','Romana', level3='Electronist aparate si echipamente', code='416', clase=1, locuri=28, romi=1, ces=1, medie=7.55)
offering(energetic,'Tehnologica','Tehnic','Electronica automatizari','Tehnician in automatizari - intensiv limba germana','Romana', level3='Electronist aparate si echipamente', is_dual=True, code='709', clase=1, locuri=28, romi=1, ces=1, medie=7.55)

# 9. Colegiul Agricol Barcianu
offering(barcianu,'Tehnologica','Resurse naturale si protectia mediului','Agricultura','Tehnician agromontan','Romana', level3='Fermier montan', code='400', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(barcianu,'Tehnologica','Resurse naturale si protectia mediului','Agricultura','Tehnician veterinar','Romana', level3='Zootehnist', code='401', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(barcianu,'Tehnologica','Resurse naturale si protectia mediului','Agricultura','Tehnician in agroturism','Romana', level3='Lucrator in agricultura ecologica', code='402', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(barcianu,'Tehnologica','Resurse naturale si protectia mediului','Protectia mediului','Tehnician ecolog si protectia calitatii mediului','Romana', is_dual=True, code='705', clase=1, locuri=30, romi=1, ces=1, medie=7.62)
offering(barcianu,'Tehnologica','Servicii','Comert','Tehnician in achizitii si contractari','Romana', level3='Comerciant - vanzator', is_dual=True, code='706', clase=1, locuri=28, romi=1, ces=1, medie=7.62)
offering(barcianu,'Tehnologica','Tehnic','Mecanica','Tehnician mecanic pentru intretinere si reparatii','Romana', level3='Mecanic auto', is_dual=True, code='707', clase=1, locuri=28, romi=1, ces=1, medie='nou')

# 10. Colegiul Economic George Baritiu
offering(baritiu,'Tehnologica','Servicii','Comert','Tehnician in activitati de comert intensiv limba germana','Romana', level3='Comerciant - vanzator', code='403', clase=1, locuri=28, romi=1, ces=1, medie=8)
offering(baritiu,'Tehnologica','Servicii','Economic','Tehnician in activitati economice - intensiv limba engleza','Romana', level3='Comerciant - vanzator', code='404', clase=1, locuri=28, romi=1, ces=1, medie=8.2)
offering(baritiu,'Tehnologica','Servicii','Economic','Tehnician in activitati economice','Romana', level3='Comerciant - vanzator', code='404', clase=2, locuri=56, romi=2, ces=2, medie=8.2)
offering(baritiu,'Tehnologica','Servicii','Economic','Tehnician in administratie','Romana', level3='Comerciant - vanzator', code='405', clase=1, locuri=28, romi=1, ces=1, medie=8.2)
offering(baritiu,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in gastronomie','Romana', level3='Bucatar', code='406', clase=0.5, locuri=14, romi=1, ces=None, medie=8.05)
offering(baritiu,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in gastronomie','Romana', level3='Ospatar (chelner) vanzator in unitati de alimentatie', code='407', clase=0.5, locuri=14, romi=None, ces=1, medie=8.05)
offering(baritiu,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in turism','Romana', level3='Lucrator hotelier', code='408', clase=1, locuri=28, romi=1, ces=1, medie=8.05)
offering(baritiu,'Tehnologica','Servicii','Comert','Tehnician in activitati de comert','Romana', level3='Comerciant - vanzator', is_dual=True, code='708', clase=1, locuri=28, romi=1, ces=1, medie=8)

# 11. Colegiul Tehnic Cibinium
offering(cibinium,'Tehnologica','Servicii','Estetica si igiena corpului omenesc','Coafor stilist','Romana', level3='Frizer - coafor - manichiurist - pedichiurist', code='409', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(cibinium,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in turism','Romana', level3='Lucrator hotelier', code='410', clase=1, locuri=28, romi=1, ces=1, medie=7.75)
offering(cibinium,'Tehnologica','Tehnic','Industrie textila si pielarie','Tehnician designer vestimentar','Romana', level3='Confectioner produse textile', code='411', clase=1, locuri=28, romi=1, ces=1, medie=7.1)
offering(cibinium,'Tehnologica','Tehnic','Industrie textila si pielarie','Tehnician in industria textila','Romana', level3='Confectioner produse textile', code='412', clase=1, locuri=28, romi=1, ces=1, medie=7.1)

# Henri Coanda (structura la Cibinium)
offering(henri,'Tehnologica','Tehnic','Mecanica','Tehnician prelucrari pe masini cu comanda numerica','Romana', level3='Operator la masini cu comanda numerica', is_dual=True, code='715', clase=2, locuri=56, romi=2, ces=2, medie=5.85)

# 12. Liceul Tehnologic Avram Iancu
offering(avramiancu,'Tehnologica','Resurse naturale si protectia mediului','Silvicultura','Tehnician in silvicultura si exploatari forestiere','Romana', level3='Padurar', code='419', clase=1, locuri=28, romi=1, ces=1, medie=6.77)
offering(avramiancu,'Tehnologica','Tehnic','Fabricarea produselor din lemn','Tehnician designer mobila si amenajari interioare','Romana', level3='Tamplar universal', code='420', clase=1, locuri=28, romi=1, ces=1, medie=7.07)
offering(avramiancu,'Tehnologica','Tehnic','Mecanica','Tehnician prelucrari pe masini cu comanda numerica','Romana', level3='Operator la masini cu comanda numerica', code='421', clase=0.5, locuri=14, romi=1, ces=None, medie='nou')
offering(avramiancu,'Tehnologica','Tehnic','Mecanica','Tehnician proiectant CAD','Romana', level3='Mecanic utilaje si instalatii in industrie', code='422', clase=0.5, locuri=14, romi=None, ces=1, medie=6.82)
offering(avramiancu,'Tehnologica','Tehnic','Electromecanica','Tehnician electromecanic','Romana', level3='Electromecanic utilaje si instalatii industriale', is_dual=True, code='712', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(avramiancu,'Tehnologica','Tehnic','Fabricarea produselor din lemn','Tehnician in prelucrarea lemnului','Romana', level3='Tamplar universal', is_dual=True, code='713', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(avramiancu,'Tehnologica','Tehnic','Mecanica','Tehnician mecatronist','Romana', level3='Mecanic echipamente hidraulice si pneumatice', is_dual=True, code='714', clase=1, locuri=28, romi=1, ces=1, medie='nou')

# 13. Liceul Tehnologic "Independenta"
offering(independenta,'Tehnologica','Servicii','Turism si alimentatie','Organizator banqueting','Romana', level3='Ospatar (chelner) vanzator in unitati de alimentatie', is_dual=True, code='716', clase=1, locuri=28, romi=1, ces=1, medie=6.27)
offering(independenta,'Tehnologica','Tehnic','Electric','Tehnician electrician electronist auto','Romana', level3='Electrician auto', is_dual=True, code='717', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Electromecanica','Tehnician electromecanic','Romana', level3='Electromecanic utilaje si instalatii industriale', is_dual=True, code='718', clase=0.5, locuri=14, romi=1, ces=None, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Electronica automatizari','Tehnician operator tehnica de calcul','Romana', level3='Electronist aparate si echipamente', is_dual=True, code='719', clase=0.5, locuri=14, romi=None, ces=1, medie=5.95)
offering(independenta,'Tehnologica','Tehnic','Mecanica','Tehnician mecatronist','Romana', level3='Mecanic echipamente hidraulice si pneumatice', is_dual=True, code='720', clase=1, locuri=28, romi=1, ces=1, medie=5.9)
offering(independenta,'Tehnologica','Tehnic','Mecanica','Tehnician prelucrari pe masini cu comanda numerica','Romana', level3='Operator la masini cu comanda numerica', is_dual=True, code='721', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Mecanica','Tehnician prelucrari pe masini cu comanda numerica','Romana', level3='Sculer-matriter', is_dual=True, code='722', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Mecanica','Tehnician transporturi','Romana', level3='Mecanic auto', is_dual=True, code='723', clase=3, locuri=84, romi=3, ces=3, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Mecanica','Tehnician transporturi','Romana', level3='Tinichigiu vopsitor auto', is_dual=True, code='724', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(independenta,'Tehnologica','Tehnic','Productie media','Tehnician operator procesare text/imagine','Romana', level3='Operator productie si exploatare film', is_dual=True, code='725', clase=0.5, locuri=14, romi=1, ces=None, medie=6.22)
offering(independenta,'Tehnologica','Tehnic','Tehnici poligrafice','Tehnician poligraf','Romana', level3='Tipăritor offset', is_dual=True, code='726', clase=0.5, locuri=14, romi=None, ces=1, medie='nou')

# 14. Liceul Tehnologic de Industrie Alimentara "Terezianum"
offering(terezianum,'Tehnologica','Resurse naturale si protectia mediului','Industrie alimentara','Tehnician analize produse alimentare','Romana', level3='Brutar - patiser - preparator produse fainoase', code='431', clase=1, locuri=28, romi=1, ces=1, medie=6.2)
offering(terezianum,'Tehnologica','Resurse naturale si protectia mediului','Industrie alimentara','Tehnician in industria alimentara','Romana', level3='Operator in industria zaharului si produselor zaharoase', code='432', clase=1, locuri=28, romi=1, ces=1, medie=6.2)
offering(terezianum,'Tehnologica','Resurse naturale si protectia mediului','Industrie alimentara','Tehnician in morarit, panificatie si produse fainoase','Romana', level3='Brutar - patiser - preparator produse fainoase', code='433', clase=1, locuri=28, romi=1, ces=1, medie=6.2)
offering(terezianum,'Tehnologica','Resurse naturale si protectia mediului','Industrie alimentara','Tehnician in prelucrarea produselor de origine animala','Romana', level3='Preparator produse din carne si peste', code='434', clase=1, locuri=28, romi=1, ces=1, medie=6.2)
offering(terezianum,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in gastronomie','Romana', level3='Bucatar', code='435', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(terezianum,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in gastronomie','Romana', level3='Cofetar-patiser', code='436', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(terezianum,'Tehnologica','Servicii','Turism si alimentatie','Tehnician in gastronomie','Romana', level3='Ospatar (chelner) vanzator in unitati de alimentatie', code='437', clase=1, locuri=28, romi=1, ces=1, medie='nou')
offering(terezianum,'Tehnologica','Tehnic','Electromecanica','Tehnician electromecanic','Romana', level3='Electromecanic utilaje si instalatii comerciale, electrocasnice si din industria alimentara', code='438', clase=1, locuri=28, romi=1, ces=1, medie=6.37)

# Rank schools 1 (best) by their highest last_admission_grade; ties share a rank.
cur.execute("""
    UPDATE schools SET grade_rank = (
        SELECT 1 + COUNT(*) FROM (
            SELECT school_id, MAX(last_admission_grade) AS best_grade
            FROM admission_offerings WHERE last_admission_grade IS NOT NULL
            GROUP BY school_id
        ) ranked
        WHERE ranked.best_grade > (
            SELECT MAX(last_admission_grade) FROM admission_offerings WHERE school_id = schools.id
        )
    )
    WHERE id IN (SELECT DISTINCT school_id FROM admission_offerings WHERE last_admission_grade IS NOT NULL)
""")

# ---------------------------------------------------------- candidates ----
# Both years sourced from evaluare.edu.ro's full county ranking (Jud=33),
# normalized to the same CSV schema (candidates_2026.csv scraped directly;
# candidates_2025.csv converted from the site's archived JSON endpoint).
_lang_normalize = {'Limba germană': 'Limba germana', 'Limba maghiară': 'Limba maghiara'}


def num_or_none(v):
    return None if v in ('-', 'Absent', '') else float(v)


def import_candidates(csv_path, year, school_year):
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        seen_codes = set()
        n_dupes = n = n_absent = 0
        for row in reader:
            code = row['code']
            if code in seen_codes:
                n_dupes += 1
                continue
            seen_codes.add(code)
            if row['media'] == 'Absent':
                n_absent += 1
                continue
            # normalize diacritics so eligibility checks against
            # native_language match consistently across both years
            native_lang = None if row['mat_lang'] == '-' else _lang_normalize.get(row['mat_lang'], row['mat_lang'])
            cur.execute("""INSERT INTO candidates
                (year, nr, idx, candidate_code, national_rank, source_school, grade_romana,
                 grade_matematica, native_language, grade_native_language, grade_average, school_year)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (year, int(row['idx']), int(row['idx']), code, int(row['pos']), row['school'],
                 num_or_none(row['rom_n']), num_or_none(row['mat_n']), native_lang,
                 num_or_none(row['mat_lang_n']), num_or_none(row['media']), school_year))
            n += 1
    print(f"candidates {year}: imported {n}, skipped {n_dupes} exact-duplicate row(s), skipped {n_absent} Absent")


import_candidates(CANDIDATES_CSV, CANDIDATES_YEAR, YEAR)
import_candidates(CANDIDATES_2025_CSV, CANDIDATES_YEAR_2025, YEAR_2025)

con.commit()

cur.execute("SELECT count(*) FROM schools")
print("schools:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM admission_offerings")
print("offerings:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM candidates")
print("candidates:", cur.fetchone()[0])
cur.execute("SELECT year, count(*) FROM candidates GROUP BY year")
print("candidates by year:", cur.fetchall())
con.close()
