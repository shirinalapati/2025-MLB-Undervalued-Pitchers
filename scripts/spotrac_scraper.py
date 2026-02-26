#!/usr/bin/env python3
"""Scrape Spotrac team payroll pages for pitcher salaries."""
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

TEAMS = {
    "dodgers": "los-angeles-dodgers",
    "yankees": "new-york-yankees",
    "mets": "new-york-mets",
    "phillies": "philadelphia-phillies",
    "astros": "houston-astros",
    "braves": "atlanta-braves",
    "padres": "san-diego-padres",
    "blue-jays": "toronto-blue-jays",
    "rangers": "texas-rangers",
    "cubs": "chicago-cubs",
    "cardinals": "st-louis-cardinals",
    "giants": "san-francisco-giants",
    "angels": "los-angeles-angels",
    "mariners": "seattle-mariners",
    "guardians": "cleveland-guardians",
    "tigers": "detroit-tigers",
    "twins": "minnesota-twins",
    "red-sox": "boston-red-sox",
    "brewers": "milwaukee-brewers",
    "white-sox": "chicago-white-sox",
    "marlins": "miami-marlins",
    "reds": "cincinnati-reds",
    "diamondbacks": "arizona-diamondbacks",
    "rays": "tampa-bay-rays",
    "orioles": "baltimore-orioles",
    "royals": "kansas-city-royals",
    "pirates": "pittsburgh-pirates",
    "nationals": "washington-nationals",
    "rockies": "colorado-rockies",
    "athletics": "oakland-athletics",
}

def scrape_team(team_slug: str) -> list[tuple[str, int]]:
    url = f"https://www.spotrac.com/mlb/{team_slug}/payroll/_/year/2025"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    # Spotrac uses various structures - try finding player rows
    # Pattern: link text is name, need to get pos (SP/RP) and salary from same row
    for a in soup.find_all("a", href=re.compile(r"/mlb/player/")):
        name = a.get_text(strip=True)
        if len(name) < 3:
            continue
        parent = a.parent
        salary = 0
        pos = ""
        for _ in range(10):
            if parent is None:
                break
            text = parent.get_text()
            # Check for position
            if not pos and (" SP " in text or " RP " in text or "| SP |" in text or "| RP |" in text or "| P |" in text):
                for part in text.split("|"):
                    part = part.strip()
                    if part in ("SP", "RP", "P") or part.startswith("SP") or part.startswith("RP"):
                        pos = part.split()[0] if " " in part else part
                        break
            # Check for salary
            m = re.search(r"\$(\d{1,3}(?:,\d{3})*)", text)
            if m:
                s = int(m.group(1).replace(",", ""))
                if 100000 < s < 500000000:
                    salary = s
                    break
            parent = parent.parent
        if salary > 0:  # Include all players; pitcher lookup uses name match
            results.append((name, salary))
    return results

def main():
    all_sal = {}
    for name, slug in TEAMS.items():
        try:
            pairs = scrape_team(slug)
            for pname, sal in pairs:
                k = pname.lower().strip()
                if sal > 0 and (k not in all_sal or sal > all_sal[k]):
                    all_sal[k] = sal
            print(f"{name}: {len(pairs)}")
        except Exception as e:
            print(f"{name}: ERROR {e}")
    # Write - keep only names that could be pitchers (we'll overwrite salaries.csv for pitcher lookup)
    out = Path(__file__).parent.parent / "public" / "data" / "salaries.csv"
    import csv
    rows = sorted(all_sal.items(), key=lambda x: -x[1])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Salary"])
        for key, sal in rows:
            display = " ".join(part.capitalize() for part in key.split())
            w.writerow([display, sal])
    print(f"Saved {len(rows)} to {out}")

if __name__ == "__main__":
    main()
