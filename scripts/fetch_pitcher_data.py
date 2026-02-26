#!/usr/bin/env python3
"""
Fetch 2025 pitcher data and compute Undervalued Pitcher Score (UPS).

Data sources:
- pybaseball (Fangraphs): Fetch starters (stats=sta) and relievers (stats=rel) separately
- Or: public/data/pitchers_raw.csv with columns Name, Team, POS (SP/RP), IP, ERA, WAR, etc.
- Salary: From salaries.csv or $5M proxy

Sample sizes (by POS column):
- Starters: POS=SP and IP >= 80
- Relievers: POS=RP and IP >= 30
"""

import json
import os
import sys
from pathlib import Path

def main():
    try:
        import pandas as pd
    except ImportError:
        print("Installing pandas...")
        os.system(f"{sys.executable} -m pip install pandas -q")
        import pandas as pd

    def parse_ip(ip_val):
        if pd.isna(ip_val):
            return 0.0
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
        for a, b in [("ó", "o"), ("í", "i"), ("é", "e"), ("á", "a"), ("ú", "u"), ("ñ", "n"), ("ü", "u")]:
            s = s.replace(a, b)
        return s

    def fetch_fg_pitchers():
        """
        Fetch starters and relievers from Fangraphs separately (stats=sta, stats=rel),
        then filter by IP: starters IP>=80, relievers IP>=30.
        Uses Fangraphs' own SP/RP split instead of GS thresholds.
        """
        from pybaseball.datasources.fangraphs import FangraphsPitchingStatsTable
        from pybaseball.enums.fangraphs import (
            FangraphsLeague,
            FangraphsMonth,
            FangraphsPositions,
            stat_list_from_str,
            stat_list_to_str,
        )

        table = FangraphsPitchingStatsTable()
        stat_columns_enums = stat_list_from_str(table.STATS_CATEGORY, "ALL")
        base_opts = {
            "pos": FangraphsPositions.parse("ALL").value,
            "lg": FangraphsLeague.parse("ALL").value,
            "qual": 0,
            "type": stat_list_to_str(stat_columns_enums),
            "season": 2025,
            "month": FangraphsMonth.parse("ALL").value,
            "season1": 2025,
            "ind": 1,
            "team": "0",
            "rost": 0,
            "age": "0,100",
            "filter": "",
            "players": "",
            "page": "1_1000",
        }

        def fetch_table(stats_type):
            opts = {**base_opts, "stats": stats_type}
            df = table.html_accessor.get_tabular_data_from_options(
                table.QUERY_ENDPOINT,
                query_params=opts,
                column_name_mapper=table.COLUMN_NAME_MAPPER,
                known_percentages=table.KNOWN_PERCENTAGES,
                row_id_func=table.ROW_ID_FUNC,
                row_id_name=table.ROW_ID_NAME,
            )
            return table._postprocess(table._validate(df))

        df_sta = fetch_table("sta")
        df_rel = fetch_table("rel")
        df_sta["IP_num"] = df_sta["IP"].apply(parse_ip)
        df_rel["IP_num"] = df_rel["IP"].apply(parse_ip)

        starters = df_sta[df_sta["IP_num"] >= 80].copy()
        relievers = df_rel[df_rel["IP_num"] >= 30].copy()
        starters["role"] = "starter"
        relievers["role"] = "reliever"
        return pd.concat([starters, relievers], ignore_index=True)

    # Prefer user CSV with POS (SP/RP) column if available
    raw_path = Path(__file__).parent.parent / "public" / "data" / "pitchers_raw.csv"
    if raw_path.exists():
        print(f"Loading from {raw_path} (expects POS column: SP=starter, RP=reliever)")
        df = pd.read_csv(raw_path)
        if "Name" not in df.columns and "Player" in df.columns:
            df = df.rename(columns={"Player": "Name"})
        if "IP" not in df.columns and "IP" not in [c.upper() for c in df.columns]:
            ip_col = next((c for c in df.columns if "IP" in c.upper() or c == "Innings"), None)
            if ip_col:
                df = df.rename(columns={ip_col: "IP"})
        df["IP_num"] = df["IP"].apply(parse_ip)
        pos_col = next((c for c in df.columns if c.upper() in ("POS", "POSITION", "ROLE")), None)
        if pos_col:
            starters = df[(df[pos_col].str.upper().str.strip() == "SP") & (df["IP_num"] >= 80)].copy()
            relievers = df[(df[pos_col].str.upper().str.strip() == "RP") & (df["IP_num"] >= 30)].copy()
            starters["role"] = "starter"
            relievers["role"] = "reliever"
            qualified = pd.concat([starters, relievers], ignore_index=True)
        else:
            print("WARNING: No POS column found. Using GS>=10 for starters, GS<10 for relievers.")
            gs = df.get("GS", pd.Series(0, index=df.index))
            starters = df[(gs >= 10) & (df["IP_num"] >= 80)].copy()
            relievers = df[(gs < 10) & (df["IP_num"] >= 30)].copy()
            starters["role"] = "starter"
            relievers["role"] = "reliever"
            qualified = pd.concat([starters, relievers], ignore_index=True)
    else:
        print("Fetching 2025 pitchers from Fangraphs (stats=sta IP>=80, stats=rel IP>=30)...")
        try:
            qualified = fetch_fg_pitchers()
        except Exception as e:
            print(f"Fangraphs sta/rel fetch failed: {e}")
            print("Falling back to pybaseball pitching_stats(qual=0) with GS>=14 for starters...")
            from pybaseball import pitching_stats
            df = pitching_stats(2025, 2025, qual=0)
            if df is None or df.empty:
                print("ERROR: No data returned. Place pitchers_raw.csv in public/data/ or check network.")
                sys.exit(1)
            df["IP_num"] = df["IP"].apply(parse_ip)
            gs = df.get("GS", pd.Series(0, index=df.index)).fillna(0).astype(float)
            starters = df[(df["IP_num"] >= 80) & (gs >= 14)].copy()
            relievers = df[(df["IP_num"] >= 30) & (gs < 14)].copy()
            starters["role"] = "starter"
            relievers["role"] = "reliever"
            qualified = pd.concat([starters, relievers], ignore_index=True)

    # Merge supplemental relievers (pitchers not in Fangraphs sta/rel)
    supplement_path = Path(__file__).parent.parent / "public" / "data" / "relief_pitchers_supplement.csv"
    if supplement_path.exists():
        try:
            sup = pd.read_csv(supplement_path)
            sup["IP_num"] = sup["IP"].apply(parse_ip)
            existing_names = {norm_key(str(n)) for n in qualified.get("Name", [])}
            added = 0
            for _, row in sup.iterrows():
                name = str(row.get("Name", "")).strip()
                if not name or norm_key(name) in existing_names or row["IP_num"] < 30:
                    continue
                ip = row["IP_num"]
                h = float(row.get("H", 0))
                bb = float(row.get("BB", 0))
                so = float(row.get("K", row.get("SO", 0)))
                tbf = max(1, 3 * ip + h + bb)
                sup_row = {
                    "Name": name,
                    "Team": str(row.get("Team", "")).strip() if pd.notna(row.get("Team")) else "",
                    "IP": row["IP"],
                    "IP_num": ip,
                    "SO": so,
                    "BB": bb,
                    "H": h,
                    "ER": float(row.get("ER", 0)),
                    "HR": float(row.get("HR", 0)),
                    "ERA": float(row.get("ERA", 5.0)),
                    "TBF": tbf,
                    "SV": float(row.get("SV", 0)),
                    "HLD": float(row.get("HLD", 0)),
                    "W": float(row.get("W", 0)),
                    "L": float(row.get("L", 0)),
                    "role": "reliever",
                }
                qualified = pd.concat([qualified, pd.DataFrame([sup_row])], ignore_index=True)
                existing_names.add(norm_key(name))
                added += 1
            if added > 0:
                print(f"Merged {added} pitchers from relief_pitchers_supplement.csv")
        except Exception as e:
            print(f"Note: Could not load relief supplement: {e}")

    if qualified.empty:
        print("ERROR: No qualified pitchers. Check data source or thresholds.")
        sys.exit(1)

    # Build computed columns when advanced stats missing
    if "FIP" not in qualified.columns:
        tbf = qualified.get("TBF", pd.Series(100, index=qualified.index))
        so = qualified.get("SO", qualified.get("K", 0))
        bb = qualified.get("BB", 0)
        hr = qualified.get("HR", 0)
        if "K%" not in qualified.columns:
            qualified["K%"] = so / tbf.replace(0, 1) * 100
        if "BB%" not in qualified.columns:
            qualified["BB%"] = bb / tbf.replace(0, 1) * 100
        qualified["FIP"] = (13 * hr + 3 * bb - 2 * so) / qualified["IP_num"].replace(0, 1) + 3.2
        qualified["SIERA"] = qualified.get("FIP", qualified["ERA"])
        qualified["xERA"] = qualified.get("xERA", qualified["ERA"])

    # Load salary override if exists (try fetch_2025_salaries if missing)
    salary_path = Path(__file__).parent.parent / "public" / "data" / "salaries.csv"
    if not salary_path.exists():
        try:
            script_dir = Path(__file__).parent
            import subprocess
            subprocess.run([sys.executable, script_dir / "fetch_2025_salaries.py"], check=False, capture_output=True)
        except Exception:
            pass

    salaries = {}
    if salary_path.exists():
        try:
            sal_df = pd.read_csv(salary_path)
            for _, row in sal_df.iterrows():
                name_key = norm_key(row.get("Name", ""))
                salaries[name_key] = float(row.get("Salary", 0))
        except Exception as e:
            print(f"Note: Could not load salaries.csv: {e}")

    team_overrides = {}
    team_path = Path(__file__).parent.parent / "public" / "data" / "team_overrides.csv"
    if team_path.exists():
        try:
            team_df = pd.read_csv(team_path)
            for _, row in team_df.iterrows():
                name_key = norm_key(row.get("Name", ""))
                team_overrides[name_key] = str(row.get("Team", "")).strip()
        except Exception as e:
            print(f"Note: Could not load team_overrides.csv: {e}")

    # Compute indices and UPS
    LEAGUE_BABIP = 0.290
    LEAGUE_LOB = 72.0
    DOLLAR_PER_WAR = 9_000_000

    def safe_float(v, default=0):
        if pd.isna(v) or v == "" or v == "-":
            return default
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    results = []
    for _, row in qualified.iterrows():
        name = str(row.get("Name", "Unknown"))
        team = str(row.get("Team", "")).strip()
        if team and "OAK" in team:
            team = team.replace("OAK", "ATH")
        if not team or team in ("- - -", "---", "--"):
            team = team_overrides.get(norm_key(name), "")
        ip = safe_float(row.get("IP_num", row.get("IP", 0)))
        era = safe_float(row.get("ERA", 5.0))
        role = row.get("role", "starter")

        # 1. Dominance Index: DI = 0.6 * (K-BB%) + 0.4 * (K%)
        k_val = safe_float(row.get("K%", row.get("K_pct", 0)))
        bb_val = safe_float(row.get("BB%", row.get("BB_pct", 0)))
        k_pct = k_val * 100 if k_val < 1 else k_val
        bb_pct = bb_val * 100 if bb_val < 1 else bb_val
        k_bb_pct = k_pct - bb_pct
        di_raw = 0.6 * k_bb_pct + 0.4 * k_pct

        # 2. Command & Control: CCI = 100 - BB%
        cci_raw = 100 - bb_pct

        # 3. Run Prevention Skill: RPSI = (1/3)*(xERA + FIP + SIERA), lower = better
        x_era = safe_float(row.get("xERA", row.get("xERA_", era)), era)
        fip = safe_float(row.get("FIP", era), era)
        siera = safe_float(row.get("SIERA", era), era)
        rpsi_raw = (x_era + fip + siera) / 3.0

        # 4. Stuff Quality: SQI = Velocity - HardHit% - Barrel%
        velo = safe_float(row.get("Velo", row.get("vFA", row.get("FBv", 90))), 90)
        hh = safe_float(row.get("HardHit%", row.get("HardHit_pct", 35)))
        barrel_raw = safe_float(row.get("Barrel%", row.get("Barrel_pct", 8)))
        hard_hit = hh * 100 if hh < 1 else hh
        barrel = barrel_raw * 100 if barrel_raw < 1 else barrel_raw
        sqi_raw = velo - hard_hit - barrel

        # 5. Luck Adjustment: LAI = (ERA−xERA)+(BABIP−LeagueBABIP)+(LOB%−LeagueLOB%)
        babip = safe_float(row.get("BABIP", row.get("BABIP_pct", 0.300)), 0.300)
        lob_raw = safe_float(row.get("LOB%", row.get("LOB_pct", 72)), 72)
        lob = lob_raw * 100 if lob_raw < 1 and lob_raw > 0 else lob_raw
        lai_raw = (era - x_era) + (babip - LEAGUE_BABIP) + (lob - LEAGUE_LOB)

        # K and BB (raw counts) for SQL/export
        # Fangraphs uses SO for strikeouts; pybaseball column mapper may differ
        k_raw = safe_float(row.get("SO", row.get("K", row.get("SO.", row.get("K.", 0)))), 0)
        bb_raw = safe_float(row.get("BB", row.get("BB.", 0)), 0)
        tbf = safe_float(row.get("TBF", row.get("PA", 0)), 0)
        if k_raw <= 0 and k_pct > 0 and tbf > 0:
            k_raw = round((k_pct / 100) * tbf)
        if bb_raw <= 0 and bb_pct > 0 and tbf > 0:
            bb_raw = round((bb_pct / 100) * tbf)
        k_count = int(k_raw)
        bb_count = int(bb_raw)

        # Traditional stats for display
        h_allowed = safe_float(row.get("H", row.get("Hits", 0)), 0)
        er_allowed = safe_float(row.get("ER", row.get("R", 0)), 0)  # R can be total runs
        hr_allowed = safe_float(row.get("HR", 0), 0)
        sv = safe_float(row.get("SV", row.get("Saves", 0)), 0)
        hld = safe_float(row.get("HLD", row.get("HLD.", row.get("Holds", 0))), 0)
        wins = safe_float(row.get("W", row.get("Wins", 0)), 0)
        losses = safe_float(row.get("L", row.get("Losses", 0)), 0)
        k_per_9 = (k_count * 9) / ip if ip > 0 else 0
        whip = (bb_count + h_allowed) / ip if ip > 0 else 0

        # 6. Salary Efficiency: SEI = WAR / Salary_Millions
        war = safe_float(row.get("WAR", 0), 0)
        # Use real salary if in CSV; else league minimum (2025: $780k)
        LEAGUE_MIN = 780_000
        salary = salaries.get(norm_key(name), LEAGUE_MIN)
        if salary <= 0:
            salary = LEAGUE_MIN
        salary_millions = salary / 1_000_000
        sei_raw = war / salary_millions if salary_millions > 0 else 0

        results.append({
            "name": name,
            "team": team,
            "role": role,
            "IP": round(ip, 1),
            "ERA": round(era, 2),
            "WAR": round(war, 2),
            "salary": round(salary, 0),
            "K": k_count,
            "BB": bb_count,
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
            "K9": round(k_per_9, 2),
            "WHIP": round(whip, 2),
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
        })

    # Normalize each index to 0-100 and compute UPS
    import numpy as np
    keys = ["DI", "CCI", "RPSI", "SQI", "LAI", "SEI"]
    arr = np.array([[r["raw"][k] for k in keys] for r in results])
    for i, key in enumerate(keys):
        col = arr[:, i]
        lo, hi = np.nanmin(col), np.nanmax(col)
        if hi - lo == 0:
            hi = lo + 1
        if key == "RPSI":  # lower is better - invert
            norm = 100 - (col - lo) / (hi - lo) * 100
        else:
            norm = (col - lo) / (hi - lo) * 100
        for j, r in enumerate(results):
            r["normalized"] = r.get("normalized", {})
            r["normalized"][key] = round(float(norm[j]), 2)

    weights = {"DI": 0.20, "CCI": 0.15, "RPSI": 0.25, "SQI": 0.10, "LAI": 0.15, "SEI": 0.15}
    for r in results:
        r["UPS"] = round(
            sum(r["normalized"][k] * w for k, w in weights.items()),
            2
        )

    # Sort by UPS descending
    results.sort(key=lambda x: x["UPS"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    # Data quality validation
    n_starters = sum(1 for r in results if r["role"] == "starter")
    n_relievers = sum(1 for r in results if r["role"] == "reliever")
    names = [r["name"] for r in results]
    duplicates = [n for n in set(names) if names.count(n) > 1]

    print("\n--- Data Quality Report ---")
    print(f"Starters (stats=sta, IP>=80): {n_starters}")
    print(f"Relievers (stats=rel, IP>=30): {n_relievers}")
    print(f"Total pitchers: {len(results)}")
    if duplicates:
        print(f"WARNING: Duplicate names (multi-team): {duplicates[:10]}{'...' if len(duplicates) > 10 else ''}")
    missing_war = sum(1 for r in results if r.get("WAR", 0) == 0)
    if missing_war > len(results) * 0.1:
        print(f"Note: {missing_war} pitchers have WAR=0 (may affect SEI)")
    print("----------------------------\n")

    out_dir = Path(__file__).parent.parent / "public" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pitchers.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} pitchers to {out_path}")
    print("Top 5 UPS:")
    for r in results[:5]:
        print(f"  {r['rank']}. {r['name']} ({r['team']}) - UPS: {r['UPS']} | {r['role']} | {r['IP']} IP")


if __name__ == "__main__":
    main()
