#!/usr/bin/env python3
"""
Build 2026 live pitcher dataset from Statcast + Baseball Reference + bWAR.

Outputs public/data/pitchers_2026.json with reliability-adjusted UPS and
low-sample flags. No IP minimum — every pitcher with Statcast data is included.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from pitcher_core import (  # noqa: E402
    DEFAULT_FB_VELO,
    apply_reliability,
    compute_raw_indices,
    mark_low_sample,
    normalize_and_score,
    norm_key,
    parse_ip,
    safe_float,
)
from team_mapping import fetch_mlb_teams_for_pitchers, resolve_team  # noqa: E402

PROJECT = SCRIPT_DIR.parent
OUT_DIR = PROJECT / "public" / "data"
SEASON = 2026


def format_name(raw: str) -> str:
    if "," in raw:
        last, first = raw.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return str(raw).strip()


def load_salaries() -> dict[str, float]:
    path = OUT_DIR / "salaries.csv"
    salaries: dict[str, float] = {}
    if not path.exists():
        return salaries
    import pandas as pd

    for _, row in pd.read_csv(path).iterrows():
        salaries[norm_key(row.get("Name", ""))] = float(row.get("Salary", 0))
    return salaries


def load_team_overrides() -> dict[str, str]:
    path = OUT_DIR / "team_overrides.csv"
    overrides: dict[str, str] = {}
    if not path.exists():
        return overrides
    import pandas as pd

    for _, row in pd.read_csv(path).iterrows():
        overrides[norm_key(row.get("Name", ""))] = str(row.get("Team", "")).strip()
    return overrides


def classify_role(gs: float, g: float) -> str:
    if gs >= 5 or (g > 0 and gs / g >= 0.5):
        return "starter"
    return "reliever"


def compute_lob(h: float, bb: float, hbp: float, r: float) -> float:
    """Rough strand-rate proxy when LOB% is unavailable."""
    denom = h + bb + hbp
    if denom <= 0:
        return 72.0
    return max(0.0, min(100.0, (denom - r) / denom * 100))


def build_dataset() -> list[dict]:
    import pandas as pd
    import pybaseball as pyb

    pyb.cache.enable()

    print(f"Fetching Statcast expected stats ({SEASON})…")
    exp = pyb.statcast_pitcher_expected_stats(SEASON, minPA=1)
    print(f"Fetching Statcast barrels ({SEASON})…")
    bar = pyb.statcast_pitcher_exitvelo_barrels(SEASON, minBBE=1)
    print(f"Fetching BRef pitching ({SEASON})…")
    bref = pyb.pitching_stats_bref(SEASON)
    print("Fetching bWAR pitching…")
    war_df = pyb.bwar_pitch()
    war26 = (
        war_df[war_df["year_ID"] == SEASON]
        .groupby("mlb_ID", as_index=False)["WAR"]
        .sum()
        .rename(columns={"mlb_ID": "player_id", "WAR": "WAR_bref"})
    )

    exp = exp.copy()
    exp["player_id"] = pd.to_numeric(exp["player_id"], errors="coerce").astype(int)
    bar["player_id"] = pd.to_numeric(bar["player_id"], errors="coerce").astype(int)
    bref["player_id"] = pd.to_numeric(bref["mlbID"], errors="coerce").astype(int)

    df = exp.merge(
        bref,
        on="player_id",
        how="inner",
        suffixes=("_sc", ""),
    )
    df = df.merge(
        bar[["player_id", "brl_percent", "ev95percent"]],
        on="player_id",
        how="left",
    )
    df = df.merge(war26, on="player_id", how="left")

    salaries = load_salaries()
    team_overrides = load_team_overrides()

    player_ids = df["player_id"].astype(int).tolist()
    print(f"Resolving team abbreviations via MLB API ({len(player_ids)} pitchers)…")
    mlb_teams = fetch_mlb_teams_for_pitchers(player_ids, SEASON)

    results: list[dict] = []
    for _, row in df.iterrows():
        sc_name = row.get("last_name, first_name")
        if sc_name is not None and str(sc_name).strip() and str(sc_name) != "nan":
            name = format_name(str(sc_name))
        else:
            name = format_name(str(row.get("Name", "Unknown")))

        pid = int(row["player_id"])
        team = resolve_team(str(row.get("Tm", "")), pid, mlb_teams)
        if not team or team in ("- - -", "---", "--"):
            team = team_overrides.get(norm_key(name), "")

        ip = parse_ip(row.get("IP", 0))
        if ip <= 0:
            continue

        gs = safe_float(row.get("GS", 0))
        g = safe_float(row.get("G", 0))
        role = classify_role(gs, g)

        so = safe_float(row.get("SO", 0))
        bb = safe_float(row.get("BB", 0))
        bf = safe_float(row.get("BF", row.get("pa", 0)))
        hr = safe_float(row.get("HR", 0))
        h = safe_float(row.get("H", 0))
        er = safe_float(row.get("ER", 0))
        r = safe_float(row.get("R", er))
        hbp = safe_float(row.get("HBP", 0))
        era = safe_float(row.get("ERA", 5.0))
        xera = safe_float(row.get("xera", era), era)
        babip = safe_float(row.get("BAbip", 0.300), 0.300)
        whip = safe_float(row.get("WHIP", 0), 0)
        if whip <= 0 and ip > 0:
            whip = (bb + h) / ip

        k_pct = (so / bf * 100) if bf > 0 else 0.0
        bb_pct = (bb / bf * 100) if bf > 0 else 0.0
        fip = (13 * hr + 3 * bb - 2 * so) / ip + 3.2 if ip > 0 else era
        siera = fip  # proxy when FanGraphs SIERA unavailable for 2026
        lob = compute_lob(h, bb, hbp, r)

        merged_row = {
            "IP_num": ip,
            "IP": ip,
            "ERA": era,
            "xERA": xera,
            "FIP": fip,
            "SIERA": siera,
            "K%": k_pct,
            "BB%": bb_pct,
            "SO": so,
            "BB": bb,
            "TBF": bf,
            "PA": bf,
            "H": h,
            "ER": er,
            "HR": hr,
            "W": safe_float(row.get("W", 0)),
            "L": safe_float(row.get("L", 0)),
            "SV": safe_float(row.get("SV", 0)),
            "HLD": 0,
            "BABIP": babip,
            "LOB%": lob,
            "WAR": safe_float(row.get("WAR_bref", 0)),
            "Velo": DEFAULT_FB_VELO,
            "HardHit%": safe_float(row.get("ev95percent", 35), 35),
            "Barrel%": safe_float(row.get("brl_percent", 8), 8),
            "role": role,
        }

        salary = salaries.get(norm_key(name), 780_000)
        if salary <= 0:
            salary = 780_000

        record = compute_raw_indices(merged_row, salary)
        record["name"] = name
        record["team"] = team
        record["player_id"] = int(row["player_id"])
        record["season"] = SEASON
        results.append(record)

    normalize_and_score(results)
    apply_reliability(results)
    return results


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = build_dataset()

    if not results:
        print("ERROR: No pitchers built.")
        return 1

    _, th_s, th_r = mark_low_sample(results)

    out_path = OUT_DIR / "pitchers_2026.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (OUT_DIR / "last_updated_2026.txt").write_text(ts)

    meta = {
        "season": SEASON,
        "full_updated": ts,
        "low_sample_threshold_starter": round(th_s, 1),
        "low_sample_threshold_reliever": round(th_r, 1),
        "pitcher_count": len(results),
    }
    (OUT_DIR / "pitchers_2026_meta.json").write_text(json.dumps(meta, indent=2))

    n_low = sum(1 for r in results if r.get("low_sample"))
    n_st = sum(1 for r in results if r["role"] == "starter")
    n_rel = sum(1 for r in results if r["role"] == "reliever")
    print(f"\nSaved {len(results)} pitchers → {out_path}")
    print(f"  Starters: {n_st} | Relievers: {n_rel} | Low sample: {n_low}")
    print(f"  Low-sample thresholds: SP {th_s:.1f} IP, RP {th_r:.1f} IP")
    print("Top 5 adjusted UPS:")
    for r in results[:5]:
        print(
            f"  {r['rank']}. {r['name']} ({r['team']}) — "
            f"adj UPS {r['adjusted_UPS']} | {r['IP']} IP | {r['role']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
