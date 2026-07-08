#!/usr/bin/env python3
"""Re-scrape 2026 Evaluare Nationala candidates for Sibiu county (Jud=33)
from evaluare.edu.ro's paginated CandFromJudIAD.aspx endpoint.

The endpoint requires an ASP.NET session cookie (a cold request 302s to
Unavailable.aspx). We first hit the site to mint a session, then page
through PageN=1.. until an empty/redirected page, writing the 15 columns
per row straight to candidates_2026.csv in the existing schema.
"""
import csv
import html as htmllib
import re
import subprocess
import sys
import time

BASE = "https://evaluare.edu.ro/Evaluare/CandFromJudIAD.aspx?Jud=33&Poz=0&PageN={}"
COOKIE_JAR = "/tmp/scrape_cj.txt"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
OUT_CSV = "/Users/robert/Library/Scripts/school-admissions/candidates_2026.csv"
HEADER = ["idx", "code", "pos", "school", "rom_n", "rom_c", "rom_f",
          "mat_n", "mat_c", "mat_f", "mat_lang", "mat_lang_n", "mat_lang_c",
          "mat_lang_f", "media"]

ROW_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
CODE_RE = re.compile(r'SB\d{5,}')


def clean(cell):
    txt = re.sub(r'<[^>]+>', '', cell)          # strip tags
    txt = htmllib.unescape(txt)                  # decode entities
    return txt.replace('\xa0', ' ').strip()


def fetch(page, warm=False):
    """Fetch one page via curl, sharing the cookie jar. Returns (http_code, html)."""
    url = BASE.format(page)
    args = ["curl", "-s", "--max-time", "40",
            "-b", COOKIE_JAR, "-c", COOKIE_JAR,
            "-H", f"User-Agent: {UA}",
            "-H", "Referer: https://evaluare.edu.ro/Evaluare/CandFromJudIAD.aspx?Jud=33&Poz=0&PageN=1",
            "-w", "\n__HTTP__%{http_code}", url]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    body, _, code = out.rpartition("__HTTP__")
    return code.strip(), body


def mint_session():
    # cold hit to obtain ASP.NET_SessionId, then confirm page 1 loads
    subprocess.run(["curl", "-s", "--max-time", "40", "-c", COOKIE_JAR,
                    "-H", f"User-Agent: {UA}",
                    "https://evaluare.edu.ro/Evaluare/Rapoarte.aspx"],
                   capture_output=True)
    code, html = fetch(1)
    return code, html


def fetch_robust(page, tries=10):
    """Fetch a page, retrying the same session on transient 302s (the server
    randomly 302s ~25% of requests; a plain same-session retry recovers).
    Re-mint only as a last resort after several same-session failures."""
    for attempt in range(tries):
        code, html = fetch(page)
        if code == "200" and parse_rows(html):
            return code, html
        time.sleep(0.4)
        if attempt and attempt % 5 == 0:  # occasional re-mint if truly stuck
            mint_session()
    return code, html


def parse_rows(html):
    rows = []
    for r in ROW_RE.findall(html):
        if not CODE_RE.search(r):
            continue
        cells = [clean(c) for c in CELL_RE.findall(r)]
        if len(cells) == 15:
            rows.append(cells)
    return rows


def main():
    code, html = mint_session()
    if code != "200" or not parse_rows(html):
        sys.exit(f"Could not load page 1 (HTTP {code}); site may have de-published the data.")

    all_rows = []
    seen = set()
    page = 1
    while True:
        if page > 1:
            code, html = fetch_robust(page)
            if code != "200":
                print(f"page {page}: HTTP {code} after retries -> stop", file=sys.stderr)
                break
        rows = parse_rows(html)
        if not rows:
            print(f"page {page}: 0 rows -> stop", file=sys.stderr)
            break
        new = 0
        for cells in rows:
            key = cells[1]  # candidate code
            if key in seen:
                continue
            seen.add(key)
            all_rows.append(cells)
            new += 1
        print(f"page {page}: {len(rows)} rows ({new} new), total {len(all_rows)}", file=sys.stderr)
        if new == 0:  # a repeat page = past the end
            break
        page += 1
        time.sleep(0.25)

    all_rows.sort(key=lambda c: int(c[0]))  # by idx
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(all_rows)
    print(f"WROTE {len(all_rows)} candidates to {OUT_CSV}")


if __name__ == "__main__":
    main()
