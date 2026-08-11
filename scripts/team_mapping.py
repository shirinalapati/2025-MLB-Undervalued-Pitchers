"""Map BRef / MLB API team names to dashboard abbreviations (match 2025 format)."""

from __future__ import annotations

import re
from typing import Any

# BRef city-only labels (unique franchises)
CITY_TO_ABBR: dict[str, str] = {
    "Arizona": "ARI",
    "Athletics": "ATH",
    "Atlanta": "ATL",
    "Baltimore": "BAL",
    "Boston": "BOS",
    "Cincinnati": "CIN",
    "Cleveland": "CLE",
    "Colorado": "COL",
    "Detroit": "DET",
    "Houston": "HOU",
    "Kansas City": "KCR",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "Philadelphia": "PHI",
    "Pittsburgh": "PIT",
    "San Diego": "SDP",
    "San Francisco": "SFG",
    "Seattle": "SEA",
    "St. Louis": "STL",
    "Tampa Bay": "TBR",
    "Texas": "TEX",
    "Toronto": "TOR",
    "Washington": "WSN",
}

AMBIGUOUS_CITIES = frozenset({"Chicago", "Los Angeles", "New York"})

MLB_TEAM_NAME_TO_ABBR: dict[str, str] = {
    "Arizona Diamondbacks": "ARI",
    "Athletics": "ATH",
    "Oakland Athletics": "ATH",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KCR",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Yankees": "NYY",
    "New York Mets": "NYM",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SDP",
    "San Francisco Giants": "SFG",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TBR",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSN",
}


def city_or_name_to_abbr(label: str) -> str:
    s = label.strip()
    if not s:
        return s
    if s in MLB_TEAM_NAME_TO_ABBR:
        return MLB_TEAM_NAME_TO_ABBR[s]
    if s in CITY_TO_ABBR:
        return CITY_TO_ABBR[s]
    if s.upper() in {v for v in CITY_TO_ABBR.values()} | set(MLB_TEAM_NAME_TO_ABBR.values()):
        return s.upper()
    return s


def split_team_tokens(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,/]", raw) if p.strip()]


def resolve_team(tm_bref: str, player_id: int | None, mlb_team_by_player: dict[int, str]) -> str:
    """
    Normalize team string to abbreviations like SFG or MIN/TBR.
    Prefer MLB API for ambiguous single-city BRef labels (Chicago, LA, NY).
    """
    raw = str(tm_bref or "").strip()
    if raw and "OAK" in raw:
        raw = raw.replace("OAK", "ATH")

    if player_id and player_id in mlb_team_by_player:
        api_abbr = mlb_team_by_player[player_id]
        if "," not in raw and raw not in AMBIGUOUS_CITIES:
            # Single-team BRef label — API is authoritative for abbrev
            if raw and split_team_tokens(raw):
                bref_parts = split_team_tokens(raw)
                if len(bref_parts) == 1:
                    mapped = city_or_name_to_abbr(bref_parts[0])
                    if mapped != bref_parts[0] and mapped == api_abbr:
                        return api_abbr
            return api_abbr

    parts = split_team_tokens(raw)
    if not parts:
        return mlb_team_by_player.get(player_id or -1, "")

    if len(parts) == 1 and parts[0] in AMBIGUOUS_CITIES and player_id:
        return mlb_team_by_player.get(player_id, city_or_name_to_abbr(parts[0]))

    abbrs = [city_or_name_to_abbr(p) for p in parts]
    return "/".join(dict.fromkeys(abbrs))


def fetch_mlb_teams_for_pitchers(player_ids: list[int], season: int) -> dict[int, str]:
    """player_id → primary season team abbreviation via MLB Stats API."""
    import pandas as pd
    import requests

    from mlb_pitcher_api import MLB_PEOPLE_URL, PEOPLE_BATCH_SIZE

    ids = sorted({int(x) for x in player_ids if pd.notna(x) and int(x) > 0})
    out: dict[int, str] = {}
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
            team = splits[0].get("team") or {}
            abbr = team.get("abbreviation")
            name = team.get("name") or ""
            if abbr:
                out[int(pid)] = str(abbr).upper()
            elif name in MLB_TEAM_NAME_TO_ABBR:
                out[int(pid)] = MLB_TEAM_NAME_TO_ABBR[name]

    return out
