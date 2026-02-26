#!/usr/bin/env python3
"""
Fetch 2025 pitcher salaries from Fangraphs RosterResource (all 30 teams).
Output: public/data/salaries.csv with Name, Salary
"""

import csv
import re
import sys
import time
from pathlib import Path

# Fangraphs RosterResource team slugs
TEAMS = [
    "athletics", "orioles", "red-sox", "white-sox", "guardians", "tigers",
    "astros", "royals", "angels", "twins", "yankees", "mariners", "rays",
    "rangers", "blue-jays", "diamondbacks", "braves", "cubs", "reds",
    "rockies", "dodgers", "marlins", "brewers", "mets", "padres", "phillies",
    "pirates", "giants", "cardinals", "nationals",
]

BASE = "https://www.fangraphs.com/roster-resource/payroll"


def fetch(url: str) -> str:
    try:
        import requests
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  Fetch failed: {e}", file=sys.stderr)
        return ""


def parse_pitcher_salaries(html: str, team: str) -> list[tuple[str, int]]:
    """Extract (name, 2025_salary) for pitchers from RosterResource HTML."""
    results = []
    # Find pitcher links: href contains /players/ and /stats/pitching
    # Format: <a href="/players/name/id/stats/pitching">Name</a>
    pitcher_pattern = re.compile(
        r'<a[^>]+href="[^"]*/(\d+)/stats/pitching"[^>]*>([^<]+)</a>',
        re.I
    )
    # Also match general player links - we'll filter by table context
    # The 2025 salary is in a table cell - look for $X,XXX,XXX patterns
    salary_pattern = re.compile(r'\$[\d,]+(?:\.\d+)?')

    # Strategy: find all rows that contain pitcher links, then get 2025 salary from that row
    # Table row: <tr>...</tr> with cells <td>...</td>
    # Split by <tr> and process each row
    for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.I):
        row_html = row.group(1)
        # Check if this row has a pitcher link
        pit_match = pitcher_pattern.search(row_html)
        if not pit_match:
            continue
        name = pit_match.group(2).strip()
        # Clean name - remove extra whitespace
        name = " ".join(name.split())
        # Find 2025 salary - table has columns: Player, Age, Service, Contract, Info, AAV, 2025, 2026...
        # Typically 6th data cell is 2025 (0-indexed: 6)
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row_html, re.DOTALL | re.I)
        salary = 0
        for i, cell in enumerate(cells):
            cell_text = re.sub(r'<[^>]+>', '', cell).strip()
            # 2025 is usually in columns 6-7 area; look for first $ that's reasonably large
            if i >= 5 and i <= 8:
                m = salary_pattern.search(cell_text.replace(',', ''))
                if m:
                    val_str = m.group(0).replace('$', '').replace(',', '')
                    try:
                        val = int(float(val_str))
                        if 100000 <= val <= 500000000:  # Sanity: $100k to $500M
                            salary = val
                            break
                    except ValueError:
                        pass
        if salary > 0:
            results.append((name, salary))
    return results


def normalize_name(s: str) -> str:
    """Handle accents - Fangraphs uses é, ü etc. Keep as-is for matching."""
    return s.strip()


def main():
    all_salaries: dict[str, int] = {}
    for team in TEAMS:
        url = f"{BASE}/{team}?season=2025"
        print(f"Fetching {team}...", end=" ", flush=True)
        html = fetch(url)
        if not html:
            print("skip")
            continue
        pairs = parse_pitcher_salaries(html, team)
        added = 0
        for name, sal in pairs:
            key = normalize_name(name).lower()
            if sal > 0 and (key not in all_salaries or sal > all_salaries[key]):
                all_salaries[key] = sal
                added += 1
        print(f"{len(pairs)} pitchers, {added} new/updated")
        time.sleep(0.5)  # Be nice to the server

    if not all_salaries:
        print("No salaries extracted.", file=sys.stderr)
        return 1

    out_path = Path(__file__).parent.parent / "public" / "data" / "salaries.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build output: preserve display name (with proper caps) from a known source
    # Use first occurrence's name for display
    seen_keys = set()
    rows = []
    for key in sorted(all_salaries.keys(), key=lambda x: -all_salaries[x]):
        sal = all_salaries[key]
        # Capitalize each word for display
        display = " ".join(w.capitalize() for w in key.split())
        rows.append((display, sal))

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Salary"])
        w.writerows(rows)

    print(f"\nSaved {len(rows)} pitcher salaries to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
