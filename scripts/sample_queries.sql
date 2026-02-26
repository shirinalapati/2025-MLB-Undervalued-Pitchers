-- Sample SQL queries for pitcher analytics
-- Run against pitchers.db: sqlite3 public/data/pitchers.db < scripts/sample_queries.sql
-- Or: sqlite3 public/data/pitchers.db and paste queries

-- 1. Top 10 undervalued pitchers by UPS
SELECT name, team, role, IP, ERA, K, BB, k_pct, BB_pct, xERA, FIP, SIERA,
       fb_velo, hardhit_pct, barrel_pct, BABIP, LOB_pct, UPS
FROM pitchers
ORDER BY UPS DESC
LIMIT 10;

-- 2. Top starters only (80+ IP equivalent via role)
SELECT name, team, IP, ERA, K, K_pct, BB_pct, xERA, FIP, fb_velo, UPS
FROM pitchers
WHERE role = 'starter'
ORDER BY UPS DESC
LIMIT 20;

-- 3. Top relievers only
SELECT name, team, IP, ERA, K, K_pct, BB_pct, xERA, FIP, fb_velo, UPS
FROM pitchers
WHERE role = 'reliever'
ORDER BY UPS DESC
LIMIT 20;

-- 4. High strikeout, low walk (K% > 25, BB% < 8)
SELECT name, team, role, K, K_pct, BB_pct, xERA, FIP, UPS
FROM pitchers
WHERE k_pct > 25 AND BB_pct < 8
ORDER BY K_pct DESC;

-- 5. Best run prevention (lowest xERA + FIP + SIERA)
SELECT name, team, role, xERA, FIP, SIERA, (xERA + FIP + SIERA) / 3.0 AS rpsi, UPS
FROM pitchers
ORDER BY rpsi ASC
LIMIT 15;

-- 6. Highest fastball velocity with 80+ IP (starters)
SELECT name, team, fb_velo, hardhit_pct, barrel_pct, ERA, UPS
FROM pitchers
WHERE role = 'starter' AND IP >= 80
ORDER BY fb_velo DESC
LIMIT 15;

-- 7. Team summary: avg UPS, count by role
SELECT team, role, COUNT(*) AS n, ROUND(AVG(UPS), 1) AS avg_ups
FROM pitchers
GROUP BY team, role
ORDER BY team, role;

-- 8. Luck candidates: ERA much higher than xERA (potentially unlucky)
SELECT name, team, role, ERA, xERA, ERA - xERA AS era_minus_xera, BABIP, LOB_pct
FROM pitchers
WHERE ERA - xERA > 0.5
ORDER BY (ERA - xERA) DESC
LIMIT 15;
