#!/usr/bin/env python3
"""
Fetch 2025 MLB pitcher salaries from Spotrac and write salaries.csv.

Output: public/data/salaries.csv with columns Name, Salary
Format: Name matches Fangraphs (First Last), Salary in dollars.

Usage: python scripts/fetch_2025_salaries.py
"""

import csv
import re
import sys
from pathlib import Path

# Spotrac 2025 salary pages for pitchers (Total Cash sort)
SPOTRAC_URLS = [
    "https://www.spotrac.com/mlb/rankings/2025/salary/starting-pitcher/",
    "https://www.spotrac.com/mlb/rankings/2025/salary/relief-pitcher/",
]


def parse_salary(s: str) -> int:
    """Parse '$42,000,000' -> 42000000."""
    s = str(s).strip().replace("$", "").replace(",", "").replace(" ", "")
    m = re.search(r"^[\d.]+", s)
    if m:
        try:
            return int(float(m.group(0)))
        except ValueError:
            pass
    return 0


def normalize_name(s: str) -> str:
    """Spotrac 'Wheeler, Zack' -> 'Zack Wheeler' for Fangraphs match."""
    s = str(s).strip()
    if "," in s:
        last, first = s.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return s


def fetch_page(url: str) -> str:
    """Fetch HTML with requests."""
    try:
        import requests
        r = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def extract_salaries(html: str, position_filter: tuple = ("SP", "RP")) -> list[tuple[str, int]]:
    """
    Extract (name, salary) from Spotrac HTML. Only include SP/RP.
    Spotrac structure: player link, team+position (e.g. "PHI, SP"), then salary.
    """
    results = []
    # Match pattern: $42,000,000 style salaries
    # Look for player names and nearby salaries; position is in Team, Pos format
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Install: pip install beautifulsoup4", file=sys.stderr)
        return results

    soup = BeautifulSoup(html, "html.parser")
    # Spotrac uses class 'rankings-player-info' or similar for rows
    rows = soup.find_all("tr", class_=re.compile(r"rankings|player"))
    if not rows:
        # Fallback: find all salary-like spans and walk up for context
        for span in soup.find_all(string=re.compile(r"\$\d[\d,]*")):
            parent = span.parent
            if not parent:
                continue
            salary = parse_salary(span)
            if salary <= 0:
                continue
            # Walk up to find player link and position
            for _ in range(10):
                if not parent:
                    break
                link = parent.find("a", href=re.compile(r"/player/"))
                if link:
                    name = normalize_name(link.get_text(strip=True))
                    # Check if nearby text has SP or RP
                    txt = parent.get_text()
                    if "SP" in txt or "RP" in txt or " P" in txt:
                        results.append((name, salary))
                    break
                parent = parent.parent
    else:
        for tr in rows:
            links = tr.find_all("a", href=re.compile(r"/player/"))
            cells = tr.find_all(["td", "span"])
            txt = tr.get_text()
            if "SP" not in txt and "RP" not in txt:
                continue
            for link in links:
                name = normalize_name(link.get_text(strip=True))
                for node in tr.find_all(string=re.compile(r"\$\d[\d,]*")):
                    salary = parse_salary(node)
                    if salary > 0:
                        results.append((name, salary))
                        break

    return results


def main():
    all_salaries: dict[str, int] = {}  # name_lower -> salary (keep highest if dup)
    for url in SPOTRAC_URLS:
        print(f"Fetching {url} ...")
        html = fetch_page(url)
        if not html:
            continue
        pairs = extract_salaries(html)
        for name, salary in pairs:
            key = name.lower().strip()
            if salary > 0 and (key not in all_salaries or salary > all_salaries[key]):
                all_salaries[key] = salary
        print(f"  Got {len(pairs)} entries")

    if not all_salaries:
        print("No salaries extracted. Create public/data/salaries.csv manually with Name,Salary", file=sys.stderr)
        return 1

    out_path = Path(__file__).parent.parent / "public" / "data" / "salaries.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Salary"])
        for name in sorted(all_salaries.keys(), key=lambda x: -all_salaries[x]):
            # Reconstruct display name (capitalize)
            display = " ".join(w.capitalize() for w in name.split())
            w.writerow([display, all_salaries[name]])
    print(f"Saved {len(all_salaries)} salaries to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
