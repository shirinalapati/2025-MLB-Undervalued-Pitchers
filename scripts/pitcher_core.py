"""
Shared UPS scoring helpers for 2025 full-season and 2026 live pipelines.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LEAGUE_BABIP = 0.290
LEAGUE_LOB = 72.0
LEAGUE_MIN_SALARY = 780_000
DEFAULT_FB_VELO = 93.0

UPS_WEIGHTS = {"DI": 0.20, "CCI": 0.15, "RPSI": 0.25, "SQI": 0.10, "LAI": 0.15, "SEI": 0.15}


def parse_ip(ip_val) -> float:
    if pd.isna(ip_val):
        return 0.0
    try:
        return float(ip_val)
    except (ValueError, TypeError):
        s = str(ip_val).strip()
        if "." in s:
            whole, frac = s.split(".", 1)
            return int(whole) + int(frac) / 3.0
        return float(s) if s else 0.0


def norm_key(s: str) -> str:
    s = str(s).strip().lower()
    for a, b in [("ó", "o"), ("í", "i"), ("é", "e"), ("á", "a"), ("ú", "u"), ("ñ", "n"), ("ü", "u")]:
        s = s.replace(a, b)
    return s


def safe_float(v, default=0.0) -> float:
    if pd.isna(v) or v == "" or v == "-":
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def compute_raw_indices(row, salary: float) -> dict:
    """Return raw index values + display fields from a merged pitcher row."""
    ip = safe_float(row.get("IP_num", row.get("IP", 0)))
    era = safe_float(row.get("ERA", 5.0))
    role = row.get("role", "starter")

    k_val = safe_float(row.get("K%", row.get("K_pct", 0)))
    bb_val = safe_float(row.get("BB%", row.get("BB_pct", 0)))
    k_pct = k_val * 100 if k_val < 1 else k_val
    bb_pct = bb_val * 100 if bb_val < 1 else bb_val
    k_bb_pct = k_pct - bb_pct
    di_raw = 0.6 * k_bb_pct + 0.4 * k_pct
    cci_raw = 100 - bb_pct

    x_era = safe_float(row.get("xERA", row.get("xera", era)), era)
    fip = safe_float(row.get("FIP", era), era)
    siera = safe_float(row.get("SIERA", fip), fip)
    rpsi_raw = (x_era + fip + siera) / 3.0

    velo = safe_float(row.get("Velo", row.get("fb_velo", row.get("vFA", DEFAULT_FB_VELO))), DEFAULT_FB_VELO)
    hh = safe_float(row.get("HardHit%", row.get("hard_hit_percent", row.get("hardhit_pct", 35))))
    barrel_raw = safe_float(row.get("Barrel%", row.get("barrel_batted_rate", row.get("barrel_pct", 8))))
    hard_hit = hh * 100 if hh < 1 else hh
    barrel = barrel_raw * 100 if barrel_raw < 1 else barrel_raw
    sqi_raw = velo - hard_hit - barrel

    babip = safe_float(row.get("BABIP", 0.300), 0.300)
    lob_raw = safe_float(row.get("LOB%", row.get("LOB_pct", 72)), 72)
    lob = lob_raw * 100 if 0 < lob_raw < 1 else lob_raw
    lai_raw = (era - x_era) + (babip - LEAGUE_BABIP) + (lob - LEAGUE_LOB)

    k_raw = safe_float(row.get("SO", row.get("K", 0)), 0)
    bb_raw = safe_float(row.get("BB", 0), 0)
    tbf = safe_float(row.get("TBF", row.get("PA", 0)), 0)
    if k_raw <= 0 and k_pct > 0 and tbf > 0:
        k_raw = round((k_pct / 100) * tbf)
    if bb_raw <= 0 and bb_pct > 0 and tbf > 0:
        bb_raw = round((bb_pct / 100) * tbf)

    h_allowed = safe_float(row.get("H", 0), 0)
    er_allowed = safe_float(row.get("ER", 0), 0)
    hr_allowed = safe_float(row.get("HR", 0), 0)
    sv = safe_float(row.get("SV", 0), 0)
    hld = safe_float(row.get("HLD", 0), 0)
    wins = safe_float(row.get("W", 0), 0)
    losses = safe_float(row.get("L", 0), 0)
    war = safe_float(row.get("WAR", 0), 0)

    salary = salary if salary > 0 else LEAGUE_MIN_SALARY
    salary_millions = salary / 1_000_000
    sei_raw = war / salary_millions if salary_millions > 0 else 0

    k9 = (k_raw * 9) / ip if ip > 0 else 0
    whip = (bb_raw + h_allowed) / ip if ip > 0 else 0

    return {
        "IP": round(ip, 1),
        "ERA": round(era, 2),
        "WAR": round(war, 2),
        "salary": round(salary, 0),
        "K": int(k_raw),
        "BB": int(bb_raw),
        "K_pct": round(k_pct, 1),
        "BB_pct": round(bb_pct, 1),
        "xERA": round(x_era, 2),
        "FIP": round(fip, 2),
        "SIERA": round(siera, 2),
        "fb_velo": round(velo, 1),
        "hardhit_pct": round(hard_hit, 1),
        "barrel_pct": round(barrel, 1),
        "BABIP": round(babip, 3),
        "LOB_pct": round(lob, 1),
        "H": int(h_allowed),
        "ER": int(er_allowed),
        "HR": int(hr_allowed),
        "SV": int(sv),
        "HLD": int(hld),
        "W": int(wins),
        "L": int(losses),
        "K9": round(k9, 2),
        "WHIP": round(whip, 2),
        "role": role,
        "raw": {
            "DI": round(di_raw, 2),
            "CCI": round(cci_raw, 2),
            "RPSI": round(rpsi_raw, 2),
            "SQI": round(sqi_raw, 2),
            "LAI": round(lai_raw, 2),
            "SEI": round(sei_raw, 4),
        },
        "components": {
            "K_pct": round(k_pct, 1),
            "BB_pct": round(bb_pct, 1),
            "K_BB_pct": round(k_bb_pct, 1),
            "xERA": round(x_era, 2),
            "FIP": round(fip, 2),
            "SIERA": round(siera, 2),
            "Velo": round(velo, 1),
            "HardHit_pct": round(hard_hit, 1),
            "Barrel_pct": round(barrel, 1),
            "BABIP": round(babip, 3),
            "LOB_pct": round(lob, 1),
        },
    }


def normalize_and_score(results: list[dict]) -> list[dict]:
    """Min-max normalize indices and compute UPS + rank."""
    if not results:
        return results
    keys = list(UPS_WEIGHTS.keys())
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
            r.setdefault("normalized", {})
            r["normalized"][key] = round(float(norm[j]), 2)

    for r in results:
        r["UPS"] = round(sum(r["normalized"][k] * UPS_WEIGHTS[k] for k in UPS_WEIGHTS), 2)

    results.sort(key=lambda x: x["UPS"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results


def apply_reliability(results: list[dict], k_starter: float = 40.0, k_reliever: float = 20.0) -> list[dict]:
    """Sample-size-adjusted UPS for live season (regress toward 50)."""
    for r in results:
        ip = safe_float(r.get("IP", 0))
        k = k_starter if r.get("role") == "starter" else k_reliever
        w = ip / (ip + k) if ip >= 0 else 0
        r["reliability_pct"] = round(w * 100, 1)
        r["adjusted_UPS"] = round(w * r["UPS"] + (1 - w) * 50.0, 2)
    results.sort(key=lambda x: x.get("adjusted_UPS", x["UPS"]), reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results


def mark_low_sample(
    results: list[dict],
    ratio: float = 0.35,
    min_starter: float = 15.0,
    min_reliever: float = 8.0,
) -> tuple[list[dict], float, float]:
    """Flag pitchers below 35% of role median IP."""
    starters = [r for r in results if r.get("role") == "starter"]
    relievers = [r for r in results if r.get("role") == "reliever"]
    med_s = float(np.median([r["IP"] for r in starters])) if starters else min_starter
    med_r = float(np.median([r["IP"] for r in relievers])) if relievers else min_reliever
    th_s = max(min_starter, med_s * ratio)
    th_r = max(min_reliever, med_r * ratio)
    for r in results:
        th = th_s if r.get("role") == "starter" else th_r
        r["low_sample"] = r["IP"] < th
        r["low_sample_threshold"] = round(th, 1)
    return results, th_s, th_r
