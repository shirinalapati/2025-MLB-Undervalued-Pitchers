#!/usr/bin/env python3
"""
Load pitchers.json into SQLite for SQL-based analysis.
Run after: python scripts/fetch_pitcher_data.py

Usage:
  python scripts/load_pitchers_to_sqlite.py

Creates: public/data/pitchers.db
"""

import json
import sqlite3
from pathlib import Path

def main():
    base = Path(__file__).parent.parent
    json_path = base / "public" / "data" / "pitchers.json"
    db_path = base / "public" / "data" / "pitchers.db"
    schema_path = base / "schema" / "pitchers.sql"

    if not json_path.exists():
        print(f"ERROR: {json_path} not found. Run scripts/fetch_pitcher_data.py first.")
        return 1

    with open(json_path) as f:
        pitchers = json.load(f)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())

    comp = lambda p, k, d=None: p.get(k, p.get("components", {}).get(k, d))
    cur = conn.cursor()
    for p in pitchers:
        cur.execute("""
            INSERT INTO pitchers (
                name, team, role, rank, UPS,
                IP, ERA, WAR, salary,
                K, BB, k_pct, BB_pct, xERA, FIP, SIERA,
                fb_velo, hardhit_pct, barrel_pct, BABIP, LOB_pct,
                raw_DI, raw_CCI, raw_RPSI, raw_SQI, raw_LAI, raw_SEI,
                norm_DI, norm_CCI, norm_RPSI, norm_SQI, norm_LAI, norm_SEI
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["name"], p["team"], p["role"], p.get("rank"), p.get("UPS"),
            p.get("IP"), p.get("ERA"), p.get("WAR"), p.get("salary"),
            p.get("K", 0), p.get("BB", 0),
            comp(p, "K_pct"), comp(p, "BB_pct"),
            comp(p, "xERA"), comp(p, "FIP"), comp(p, "SIERA"),
            comp(p, "fb_velo") or comp(p, "Velo"),
            comp(p, "hardhit_pct") or comp(p, "HardHit_pct"),
            comp(p, "barrel_pct") or comp(p, "Barrel_pct"),
            comp(p, "BABIP"), comp(p, "LOB_pct"),
            p["raw"]["DI"], p["raw"]["CCI"], p["raw"]["RPSI"],
            p["raw"]["SQI"], p["raw"]["LAI"], p["raw"]["SEI"],
            p["normalized"]["DI"], p["normalized"]["CCI"], p["normalized"]["RPSI"],
            p["normalized"]["SQI"], p["normalized"]["LAI"], p["normalized"]["SEI"],
        ))
    conn.commit()
    conn.close()

    print(f"Loaded {len(pitchers)} pitchers into {db_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
