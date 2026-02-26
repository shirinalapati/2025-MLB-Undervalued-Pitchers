-- Pitchers table schema for Undervalued Pitcher Score (UPS) analytics
-- Load from pitchers.json via scripts/load_pitchers_to_sqlite.py

CREATE TABLE IF NOT EXISTS pitchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('starter', 'reliever')),
    rank INTEGER,
    UPS REAL,

    -- Traditional stats
    IP REAL,
    ERA REAL,
    WAR REAL,
    salary REAL,

    -- Raw component stats (for filtering/analysis)
    K INTEGER,
    BB INTEGER,
    k_pct REAL,
    BB_pct REAL,
    xERA REAL,
    FIP REAL,
    SIERA REAL,
    fb_velo REAL,
    hardhit_pct REAL,
    barrel_pct REAL,
    BABIP REAL,
    LOB_pct REAL,

    -- Index values (raw)
    raw_DI REAL,
    raw_CCI REAL,
    raw_RPSI REAL,
    raw_SQI REAL,
    raw_LAI REAL,
    raw_SEI REAL,

    -- Index values (normalized 0-100)
    norm_DI REAL,
    norm_CCI REAL,
    norm_RPSI REAL,
    norm_SQI REAL,
    norm_LAI REAL,
    norm_SEI REAL
);

CREATE INDEX IF NOT EXISTS idx_pitchers_role ON pitchers(role);
CREATE INDEX IF NOT EXISTS idx_pitchers_team ON pitchers(team);
CREATE INDEX IF NOT EXISTS idx_pitchers_UPS ON pitchers(UPS DESC);
CREATE INDEX IF NOT EXISTS idx_pitchers_K ON pitchers(K);
CREATE INDEX IF NOT EXISTS idx_pitchers_ERA ON pitchers(ERA);
