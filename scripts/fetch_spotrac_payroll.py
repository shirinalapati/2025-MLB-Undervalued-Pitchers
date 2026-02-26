#!/usr/bin/env python3
"""
Fetch 2025 Payroll Annual from Spotrac for all pitchers.
Uses Spotrac's "Payroll Annual" (same as shown in Payroll section on player pages).
Output: updates public/data/salaries.csv
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


NAME_VARIANTS = {
    "cristopher": "christopher",
    "jacob degrom": "jacob de grom",
    "de grom": "degrom",
}


def norm_name(s: str) -> str:
    s = str(s).strip().lower()
    for a, b in [("ó", "o"), ("í", "i"), ("é", "e"), ("á", "a"), ("ú", "u"), ("ñ", "n"), ("ü", "u"), ("'", ""), (".", "")]:
        s = s.replace(a, b)
    return s


def lookup_id(name: str, id_map: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    """Find Spotrac (display, pid) by pitcher name, trying variants if needed."""
    key = norm_name(name)
    if key in id_map:
        return id_map[key]
    for var_from, var_to in NAME_VARIANTS.items():
        if var_from in key:
            alt = key.replace(var_from, var_to)
            if alt in id_map:
                return id_map[alt]
        if var_to in key:
            alt = key.replace(var_to, var_from)
            if alt in id_map:
                return id_map[alt]
    return None


def name_to_slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "").replace("é", "e").replace("í", "i").replace("ó", "o").replace("á", "a").replace("ú", "u").replace("ñ", "n")


def fetch_spotrac_ids() -> dict[str, tuple[str, str]]:
    """Get player name -> Spotrac ID from rankings page."""
    url = "https://www.spotrac.com/mlb/rankings/player/_/year/2025/position/p/sort/cap_total"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    matches = re.findall(r'/redirect/player/(\d+)[^"]*"[^>]*>([^<]+)<', r.text)
    by_norm = {}
    for pid, name in matches:
        n = name.strip()
        if len(n) > 2:
            key = norm_name(n)
            if key not in by_norm:
                by_norm[key] = (n, pid)
    return {k: (display, pid) for k, (display, pid) in by_norm.items()}


def get_2025_payroll(pid: str, slug: str) -> int | None:
    """Fetch player page and extract 2025 Payroll Annual from contract table."""
    url = f"https://www.spotrac.com/mlb/player/_/id/{pid}/{slug}/"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # Find tables with a Payroll column (PayrollAnnual, Payroll Salary, etc.)
        for table in soup.find_all("table"):
            header_row = table.find("thead")
            if not header_row:
                header_row = table.find("tr")
            if not header_row:
                continue
            headers = [h.get_text(strip=True).lower() for h in header_row.find_all(["th", "td"])]
            payroll_col = None
            for i, h in enumerate(headers):
                if "payroll" in h and "luxury" not in h and "tax" not in h:
                    payroll_col = i
                    break
            if payroll_col is None:
                continue
            for tr in table.find_all("tr")[1:]:
                cells = tr.find_all(["td", "th"])
                if not cells or cells[0].get_text(strip=True) != "2025":
                    continue
                if payroll_col < len(cells):
                    cell_text = cells[payroll_col].get_text(strip=True)
                    m = re.search(r"\$?([\d,]+)", cell_text.replace("$", ""))
                    if m:
                        val = int(m.group(1).replace(",", ""))
                        if 500000 <= val <= 50000000:
                            return val
        # Fallback: use max amount in 1M-25M from 2025 row (payroll typically > base)
        for tr in soup.find_all("tr"):
            if tr.find("th"):  # skip header rows
                continue
            cells = tr.find_all("td")
            if not cells or cells[0].get_text(strip=True) != "2025":
                continue
            amounts = re.findall(r"\$([\d,]+)", tr.get_text())
            valid = [int(a.replace(",", "")) for a in amounts if 1_000_000 <= int(a.replace(",", "")) <= 25_000_000]
            if valid:
                return max(valid)
    except Exception:
        pass
    return None


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Fetch 2025 Payroll Annual from Spotrac")
    ap.add_argument("--limit", type=int, default=0, help="Max pitchers to fetch (0=all)")
    args = ap.parse_args()

    print("Fetching Spotrac pitcher IDs...", flush=True)
    id_map = fetch_spotrac_ids()
    print(f"  Found {len(id_map)} players", flush=True)

    pitchers_path = Path(__file__).parent.parent / "public" / "data" / "pitchers.json"
    with open(pitchers_path) as f:
        pitchers = json.load(f)
    if args.limit:
        pitchers = pitchers[: args.limit]
        print(f"  Limited to {len(pitchers)} pitchers", flush=True)

    salaries: dict[str, tuple[str, int]] = {}
    seen = set()
    total = len(pitchers)
    for i, p in enumerate(pitchers):
        name = p["name"]
        key = norm_name(name)
        if key in seen:
            continue
        seen.add(key)
        entry = lookup_id(name, id_map)
        if not entry:
            salaries[key] = (name, 780_000)
            continue
        display, pid = entry
        slug = name_to_slug(display)
        salary = get_2025_payroll(pid, slug)
        # Use original name for CSV so fetch_pitcher_data can match (Fangraphs spelling)
        salaries[key] = (name, salary if salary else 780_000)
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{total}...", flush=True)
        time.sleep(0.4)

    out = Path(__file__).parent.parent / "public" / "data" / "salaries.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(salaries.values(), key=lambda x: -x[1])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Name", "Salary"])
        for display_name, sal in rows:
            w.writerow([display_name, sal])
    print(f"Saved {len(rows)} salaries (Spotrac 2025 Payroll Annual) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
