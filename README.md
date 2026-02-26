# 2025 Undervalued Pitchers Dashboard

A React dashboard that ranks MLB pitchers using an **interpretable predictive model** — the **Undervalued Pitcher Score (UPS)**. Designed for baseball analytics workflows: identify undervalued talent using six transparent indices.

## Methodology

UPS is a weighted composite of six indices, each normalized to 0–100. The model prioritizes **interpretability**: every component is explainable and tied to measurable stats.

| Index | Weight | Formula | Rationale |
|-------|--------|---------|------------|
| **DI** (Dominance) | 20% | 0.6×(K-BB%) + 0.4×(K%) | Strikeout ability minus walks; primary indicator of swing-and-miss |
| **CCI** (Command & Control) | 15% | 100 − BB% | Control and walk avoidance |
| **RPSI** (Run Prevention Skill) | 25% | avg(xERA, FIP, SIERA) | Skill-based run prevention; lower is better (inverted in normalization) |
| **SQI** (Stuff Quality) | 10% | Velo − HardHit% − Barrel% | Raw stuff vs. contact quality allowed |
| **LAI** (Luck Adjustment) | 15% | (ERA−xERA) + BABIP + LOB vs. league | Separates skill from batted-ball luck |
| **SEI** (Salary Efficiency) | 15% | Performance / Salary | Value for cost; uses WAR when available |

**UPS** = 0.20×DI + 0.15×CCI + 0.25×RPSI + 0.10×SQI + 0.15×LAI + 0.15×SEI

---

## Data Sources

| Source | Use | Notes |
|--------|-----|-------|
| **FanGraphs** (via pybaseball) | Pitching stats (IP, ERA, WAR, FIP, xERA, K%, BB%, etc.) | Primary; `stats=pit`, `qual=0` for full population |
| **pitchers_raw.csv** | Optional override with custom POS (SP/RP) | Export from FanGraphs if desired |
| **salaries.csv** | Optional salary override | Overrides $5M proxy; improves SEI accuracy |

### Sample Size (Qualification)

- **Starters:** IP ≥ 80 and GS ≥ 14 → ~143 pitchers in 2025  
- **Relievers:** IP ≥ 30 and GS &lt; 14 → ~317 pitchers in 2025  

Thresholds ensure meaningful sample sizes while excluding minimal-usage arms.

---

## Setup

1. **Install dependencies**

   ```bash
   npm install
   ```

2. **Fetch pitcher data**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install pybaseball pandas numpy
   python scripts/fetch_pitcher_data.py
   ```

3. **Run the app**

   ```bash
   npm run dev
   ```

   Open [http://localhost:5173](http://localhost:5173).

---

## Salary Override

Place `public/data/salaries.csv` with `Name` and `Salary` to improve SEI accuracy:

```csv
Name,Salary
Paul Skenes,750000
Tarik Skubal,2500000
```

---

## SQL Analytics

Load the data into SQLite for querying:

```bash
python scripts/load_pitchers_to_sqlite.py
```

Creates `public/data/pitchers.db`. Run sample queries:

```bash
sqlite3 public/data/pitchers.db < scripts/sample_queries.sql
```

Schema: `schema/pitchers.sql`

---

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite  
- **Data pipeline:** Python, pybaseball (FanGraphs), pandas  
- **Database:** SQLite (optional, for SQL analytics)  
- **Model:** Interpretable composite scoring (RPSI/FIP/xERA-based)
