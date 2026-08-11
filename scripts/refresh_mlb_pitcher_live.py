#!/usr/bin/env python3
"""
Near-live refresh: MLB Stats API → merge into pitchers_2026.json.

Updates IP, ERA, and counting stats every ~2 hours. Raw UPS is NOT
recalculated here — most UPS inputs (xERA, SIERA, barrel%, hard-hit%, WAR)
come from Statcast. Only Reliability % and Adj. UPS shift with new IP.
Full UPS refresh runs via fetch_2026_pitcher_data.py (Statcast, ~4× daily).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from mlb_pitcher_api import fetch_pitching_for_player_ids, merge_live_into_records  # noqa: E402
from pitcher_core import apply_reliability, mark_low_sample  # noqa: E402

PROJECT = SCRIPT_DIR.parent
OUT_DIR = PROJECT / "public" / "data"
SEASON = 2026
DATA_PATH = OUT_DIR / "pitchers_2026.json"
TIMESTAMP_PATH = OUT_DIR / "last_updated_mlb_live_2026.txt"
META_PATH = OUT_DIR / "pitchers_2026_meta.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)


def main() -> int:
    if not DATA_PATH.exists():
        log.error("Missing %s — run scripts/fetch_2026_pitcher_data.py first.", DATA_PATH)
        return 1

    with open(DATA_PATH) as f:
        records: list[dict] = json.load(f)
    if not records:
        log.error("pitchers_2026.json is empty.")
        return 1

    pids = [int(r["player_id"]) for r in records if r.get("player_id")]
    log.info("Fetching MLB Stats API pitching for %d pitchers…", len(pids))
    mlb = fetch_pitching_for_player_ids(pids, SEASON)
    if mlb.empty:
        log.error("MLB API returned no rows.")
        return 1

    records = merge_live_into_records(records, mlb)
    apply_reliability(records)
    _, th_s, th_r = mark_low_sample(records)

    with open(DATA_PATH, "w") as f:
        json.dump(records, f, indent=2)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    TIMESTAMP_PATH.write_text(ts)

    meta = {}
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text())
    meta.update({
        "mlb_live_updated": ts,
        "low_sample_threshold_starter": round(th_s, 1),
        "low_sample_threshold_reliever": round(th_r, 1),
        "pitcher_count": len(records),
    })
    META_PATH.write_text(json.dumps(meta, indent=2))

    log.info("Saved %d pitchers → %s", len(records), DATA_PATH)
    log.info("MLB live timestamp: %s", ts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
