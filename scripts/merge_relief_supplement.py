#!/usr/bin/env python3
"""
Merge relief_pitchers_supplement.csv into pitchers.json without re-fetching from Fangraphs.
Run this after fetch_pitcher_data.py to add missing relievers, or standalone to update existing JSON.
"""

import csv
import json
from pathlib import Path

def parse_ip(ip_val):
    try:
        v = float(ip_val)
        return v
    except (ValueError, TypeError):
        s = str(ip_val).strip()
        if "." in s:
            whole, frac = s.split(".", 1)
            return int(whole) + int(frac) / 3.0
        return float(s) if s else 0.0

def norm_key(s):
    s = str(s).strip().lower()
    for a, b in [("ó","o"),("í","i"),("é","e"),("á","a"),("ú","u"),("ñ","n"),("ü","u")]:
        s = s.replace(a, b)
    return s

def main():
    base = Path(__file__).parent.parent
    data_path = base / "public" / "data" / "pitchers.json"
    supplement_path = base / "public" / "data" / "relief_pitchers_supplement.csv"
    salary_path = base / "public" / "data" / "salaries.csv"

    with open(data_path) as f:
        results = json.load(f)

    existing = {norm_key(p["name"]) for p in results}
    LEAGUE_MIN = 780_000
    salaries = {}
    if salary_path.exists():
        with open(salary_path) as f:
            for row in csv.DictReader(f):
                salaries[norm_key(row.get("Name",""))] = float(row.get("Salary", LEAGUE_MIN))

    def safe_float(v, default=0):
        if v is None or v == "" or v == "-":
            return default
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    added = []
    with open(supplement_path) as f:
        for row in csv.DictReader(f):
            name = str(row.get("Name","")).strip()
            if not name or norm_key(name) in existing:
                continue
            ip = parse_ip(row.get("IP", 0))
            if ip < 30:
                continue
            k = int(safe_float(row.get("K", 0)))
            bb = int(safe_float(row.get("BB", 0)))
            h = int(safe_float(row.get("H", 0)))
            er = int(safe_float(row.get("ER", 0)))
            hr = int(safe_float(row.get("HR", 0)))
            era = safe_float(row.get("ERA", 5.0))
            team = str(row.get("Team", "")).strip()
            sv = int(safe_float(row.get("SV", 0)))
            hld = int(safe_float(row.get("HLD", 0)))
            w = int(safe_float(row.get("W", 0)))
            l = int(safe_float(row.get("L", 0)))
            whip = (bb + h) / ip if ip > 0 else 0
            k9 = (k * 9) / ip if ip > 0 else 0
            tbf = max(1, 3 * ip + h + bb)
            k_pct = (k / tbf) * 100
            bb_pct = (bb / tbf) * 100
            fip = (13 * hr + 3 * bb - 2 * k) / ip + 3.2 if ip > 0 else era
            salary = salaries.get(norm_key(name), LEAGUE_MIN)
            war = 0
            sei_raw = war / (salary / 1e6) if salary > 0 else 0

            rec = {
                "name": name,
                "team": team,
                "role": "reliever",
                "IP": round(ip, 1),
                "ERA": round(era, 2),
                "WAR": round(war, 2),
                "salary": round(salary, 0),
                "K": k,
                "BB": bb,
                "K_pct": round(k_pct, 1),
                "BB_pct": round(bb_pct, 1),
                "xERA": round(era, 2),
                "FIP": round(fip, 2),
                "SIERA": round(fip, 2),
                "fb_velo": 90.0,
                "hardhit_pct": 35.0,
                "barrel_pct": 8.0,
                "BABIP": 0.290,
                "LOB_pct": 72.0,
                "H": h,
                "ER": er,
                "HR": hr,
                "SV": sv,
                "HLD": hld,
                "W": w,
                "L": l,
                "K9": round(k9, 2),
                "WHIP": round(whip, 2),
                "raw": {
                    "DI": round(0.6 * (k_pct - bb_pct) + 0.4 * k_pct, 2),
                    "CCI": round(100 - bb_pct, 2),
                    "RPSI": round((era + fip + fip) / 3, 2),
                    "SQI": round(90 - 35 - 8, 2),
                    "LAI": 0,
                    "SEI": round(sei_raw, 4),
                },
                "components": {},
                "normalized": {},
                "UPS": 0,
                "rank": 0,
            }
            results.append(rec)
            existing.add(norm_key(name))
            added.append(name)

    if not added:
        print("No new pitchers to add.")
        return

    # Re-normalize and re-rank all pitchers
    import numpy as np
    keys = ["DI", "CCI", "RPSI", "SQI", "LAI", "SEI"]
    arr = np.array([[r["raw"][k] for k in keys] for r in results])
    for i, key in enumerate(keys):
        col = arr[:, i]
        lo, hi = np.nanmin(col), np.nanmax(col)
        if hi - lo == 0:
            hi = lo + 1
        if key == "RPSI":
            norm = 100 - (col - lo) / (hi - lo) * 100
        else:
            norm = (col - lo) / (hi - lo) * 100
        for j, r in enumerate(results):
            r["normalized"][key] = round(float(norm[j]), 2)

    weights = {"DI": 0.20, "CCI": 0.15, "RPSI": 0.25, "SQI": 0.10, "LAI": 0.15, "SEI": 0.15}
    for r in results:
        r["UPS"] = round(sum(r["normalized"][k] * w for k, w in weights.items()), 2)

    results.sort(key=lambda x: x["UPS"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    with open(data_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Added {len(added)} pitchers: {', '.join(added[:5])}{'...' if len(added) > 5 else ''}")
    print(f"Saved {len(results)} pitchers to {data_path}")

if __name__ == "__main__":
    main()
