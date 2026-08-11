"""
Fetch season pitching stats from the public MLB Stats API (statsapi.mlb.com).
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests

log = logging.getLogger(__name__)

MLB_STATS_URL = "https://statsapi.mlb.com/api/v1/stats"
MLB_PEOPLE_URL = "https://statsapi.mlb.com/api/v1/people"
PEOPLE_BATCH_SIZE = 50

MLB_TO_COL = {
    "inningsPitched": "ip",
    "era": "era",
    "whip": "whip",
    "strikeOuts": "k",
    "baseOnBalls": "bb",
    "hits": "h",
    "earnedRuns": "er",
    "runs": "r",
    "homeRuns": "hr",
    "saves": "sv",
    "holds": "hld",
    "wins": "w",
    "losses": "l",
    "gamesStarted": "gs",
    "gamesPitched": "g",
    "hitByPitch": "hbp",
    "battersFaced": "bf",
}


def _parse_split(split: dict[str, Any]) -> dict[str, Any] | None:
    player = split.get("player") or {}
    pid = player.get("id")
    if pid is None:
        return None
    row: dict[str, Any] = {"player_id": int(pid)}
    stat = split.get("stat") or {}
    for mlb_key, col in MLB_TO_COL.items():
        val = stat.get(mlb_key)
        if val is not None and val != "":
            row[col] = val
    return row


def fetch_pitching_for_player_ids(player_ids: list[int], season: int) -> pd.DataFrame:
    ids = sorted({int(x) for x in player_ids if pd.notna(x) and int(x) > 0})
    if not ids:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    hydrate = f"stats(group=pitching,type=season,season={season})"

    for i in range(0, len(ids), PEOPLE_BATCH_SIZE):
        batch = ids[i : i + PEOPLE_BATCH_SIZE]
        resp = requests.get(
            MLB_PEOPLE_URL,
            params={"personIds": ",".join(str(x) for x in batch), "hydrate": hydrate},
            timeout=90,
        )
        resp.raise_for_status()
        for person in resp.json().get("people") or []:
            pid = person.get("id")
            if pid is None:
                continue
            stats_list = person.get("stats") or []
            if not stats_list:
                continue
            splits = stats_list[0].get("splits") or []
            if not splits:
                continue
            split = {"player": {"id": pid}, "stat": splits[0].get("stat") or {}}
            row = _parse_split(split)
            if row and row.get("ip"):
                rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["player_id"] = df["player_id"].astype(int)
    for col in MLB_TO_COL.values():
        if col in df.columns and col not in ("era", "whip", "ip"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("era", "whip", "ip"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    log.info("MLB API pitching: %d/%d pitchers with IP for %s", len(df), len(ids), season)
    return df


def merge_live_into_records(records: list[dict], mlb: pd.DataFrame) -> list[dict]:
    """
    Update counting stats from MLB API only.

    Raw UPS and index scores are left unchanged until the full Statcast refresh
    (fetch_2026_pitcher_data.py), because most UPS inputs are advanced metrics.
    Reliability % and Adj. UPS are recomputed afterward from the frozen Raw UPS
    and the new IP.
    """
    if not records or mlb.empty:
        return records

    live = mlb.set_index("player_id").to_dict("index")
    updated = 0
    for rec in records:
        pid = rec.get("player_id")
        if pid is None or pid not in live:
            continue
        row = live[pid]
        ip = float(row.get("ip") or rec.get("IP") or 0)
        if ip <= 0:
            continue

        k = float(row.get("k") or rec.get("K") or 0)
        bb = float(row.get("bb") or rec.get("BB") or 0)
        h = float(row.get("h") or rec.get("H") or 0)
        er = float(row.get("er") or rec.get("ER") or 0)
        hr = float(row.get("hr") or rec.get("HR") or 0)
        bf = float(row.get("bf") or rec.get("TBF") or 0)
        era = float(row.get("era") or rec.get("ERA") or 5)

        rec["IP"] = round(ip, 1)
        rec["ERA"] = round(era, 2)
        rec["K"] = int(k)
        rec["BB"] = int(bb)
        rec["H"] = int(h)
        rec["ER"] = int(er)
        rec["HR"] = int(hr)
        rec["SV"] = int(row.get("sv") or rec.get("SV") or 0)
        rec["HLD"] = int(row.get("hld") or rec.get("HLD") or 0)
        rec["W"] = int(row.get("w") or rec.get("W") or 0)
        rec["L"] = int(row.get("l") or rec.get("L") or 0)

        if bf > 0:
            rec["K_pct"] = round(k / bf * 100, 1)
            rec["BB_pct"] = round(bb / bf * 100, 1)
        rec["K9"] = round((k * 9) / ip, 2) if ip > 0 else 0
        rec["WHIP"] = round(float(row.get("whip") or (bb + h) / ip), 2) if ip > 0 else rec.get("WHIP", 0)
        if ip > 0:
            rec["FIP"] = round((13 * hr + 3 * bb - 2 * k) / ip + 3.2, 2)

        gs = float(row.get("gs") or 0)
        g = float(row.get("g") or 0)
        if gs >= 5 or (g > 0 and gs / g >= 0.5):
            rec["role"] = "starter"
        elif g > 0:
            rec["role"] = "reliever"

        # Keep display components in sync for stats tabs (UPS indices unchanged)
        comp = rec.get("components") or {}
        if rec.get("K_pct") is not None:
            comp["K_pct"] = rec["K_pct"]
            comp["BB_pct"] = rec.get("BB_pct", comp.get("BB_pct"))
            comp["K_BB_pct"] = round((rec["K_pct"] or 0) - (rec["BB_pct"] or 0), 1)
        if rec.get("FIP") is not None:
            comp["FIP"] = rec["FIP"]
        rec["components"] = comp
        updated += 1

    log.info("Merged MLB live counting stats into %d pitcher records (UPS frozen)", updated)
    return records


def compute_raw_indices(row: dict, salary: float) -> dict:
    from pitcher_core import compute_raw_indices as _core

    return _core(row, salary)
