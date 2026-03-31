# Undervalued Pitcher Score (UPS): A Framework for Identifying Pitching Market Inefficiencies in the 2025 MLB Season

**Author:** Shirin Alapati  
**Project:** 2025 MLB Undervalued Pitchers Dashboard  
**Date:** Offseason 2025–2026  

---

## Executive Summary

Modern baseball front offices have increasingly moved away from surface-level statistics like ERA and win totals as primary decision-making inputs. Traditional metrics are highly susceptible to defensive variance, batted-ball luck, and sequencing effects that obscure true pitcher skill. This paper presents the Undervalued Pitcher Score (UPS), a composite scoring framework designed to surface pitchers whose underlying performance metrics suggest greater future value than conventional statistics or current contract size might imply.

The UPS is constructed from six interpretable indices, each grounded in publicly available advanced metrics, normalized to a common 0–100 scale, and weighted according to predictive stability and relevance to sustainable performance. The model covers 400+ pitchers from the 2025 MLB season and is designed to be applied in roster decision-making, contract evaluation, and trade analysis contexts.

---

## 1. Motivation and Problem Statement

Front offices frequently encounter a fundamental valuation problem: a pitcher with a 2.90 ERA may be perceived as elite when their underlying metrics (xERA of 4.30, below-average strikeout rate, high BABIP suppression driven by defense) suggest significant regression risk. Conversely, a pitcher posting a 4.40 ERA with a 3.20 xERA, strong K-BB%, and above-average strand rate may be undervalued by the market due to poor surface-level results.

The gap between results-based and skill-based evaluation creates actionable market inefficiencies — buy-low opportunities on pitchers whose true performance has been masked and sell-high signals on pitchers whose numbers have been propped up by favorable variance. The UPS framework is designed to quantify and rank these inefficiencies systematically.

---

## 2. Data Sources and Sample Construction

**Pitching statistics** were retrieved from FanGraphs via the `pybaseball` library, querying starters and relievers separately using FanGraphs' native leaderboard splits:
- Starters (`stats=sta`): minimum 80 innings pitched
- Relievers (`stats=rel`): minimum 30 innings pitched

These thresholds were chosen to ensure meaningful sample sizes while excluding pitchers with insufficient data to evaluate performance patterns. The combined dataset covers approximately 400 qualified pitchers.

**Salary data** was retrieved from Spotrac via web scraping, pulling 2025 Annual Average Values (AAV) from the payroll rankings and individual player pages. Names were normalized programmatically to account for accented characters and spelling variants across data sources. Pitchers without a public salary record were assigned the 2025 MLB league minimum of $780,000.

**Supplemental data** for relievers not appearing in FanGraphs' leaderboards was collected manually and merged via a structured CSV, ensuring completeness for the full qualifying population.

---

## 3. Model Architecture: The Six Indices

The UPS is a weighted composite of six indices. Each index is computed from raw statistics, then normalized to a 0–100 range before weighting. This normalization eliminates unit bias across metrics that operate on fundamentally different scales (e.g., ERA near 3.5, K% near 22%, velocity near 93 mph).

### 3.1 Run Prevention Skill Index (RPSI) — Weight: 25%

**Formula:** `RPSI = (xERA + FIP + SIERA) / 3`

The RPSI carries the highest weight because it most directly measures a pitcher's defense-independent ability to prevent runs. ERA is omitted from this index intentionally — it incorporates defensive performance, sequencing luck, and park effects. xERA uses exit velocity and launch angle to estimate expected earned runs. FIP isolates strikeouts, walks, and home runs. SIERA further corrects for batted-ball type and infield fly rate. Averaging all three produces a robust, multi-model estimate of true run prevention skill.

The RPSI is inverted during normalization (lower is better), so a pitcher with an RPSI of 3.00 receives a higher normalized score than one at 4.50.

### 3.2 Dominance Index (DI) — Weight: 20%

**Formula:** `DI = 0.6 × (K−BB%) + 0.4 × (K%)`

Strikeout ability is one of the strongest and fastest-stabilizing predictors of pitcher success. The K-BB% differential captures a pitcher's ability to accumulate strikeouts while limiting walks, reflecting both dominance and efficiency. Pure K% is included as a secondary component because high-strikeout pitchers consistently outperform their surface results over the long run. The 0.6 weighting on K-BB% emphasizes that strikeouts alone are less valuable if paired with elevated walk rates.

### 3.3 Command and Control Index (CCI) — Weight: 15%

**Formula:** `CCI = 100 − BB%`

While walk rate is partially captured in the DI, command receives its own index because walk suppression independently drives performance sustainability. Pitchers with strong command profiles create more favorable counts, protect leads in high-leverage situations, and are less prone to inning-extending damage. The formula is intentionally simple: lower walk rate maps linearly to a higher CCI.

### 3.4 Luck Adjustment Index (LAI) — Weight: 15%

**Formula:** `LAI = (ERA − xERA) + (BABIP − League BABIP) + (LOB% − League LOB%)`

The LAI is the model's core mechanism for identifying regression candidates. A pitcher with a large positive ERA−xERA gap has outperformed their expected metrics, suggesting results may not be sustainable. A BABIP significantly below the league average (.290) often indicates favorable defensive or sequencing variance. A below-average LOB% suggests runs are being surrendered in clusters beyond what skill alone would predict. Together, these three signals construct a composite luck profile.

A positive LAI indicates a pitcher who has been unlucky and may be undervalued. A negative LAI indicates potential overperformance. The index is weighted at 15% because luck signals are diagnostic, not predictive — they identify candidates for further evaluation, but weak underlying skill cannot be rescued by luck regression alone.

### 3.5 Salary Efficiency Index (SEI) — Weight: 15%

**Formula:** `SEI = WAR / Salary (in millions)`

The SEI quantifies surplus value: the amount of production generated per payroll dollar. This is central to modern roster construction. A reliever producing 2.0 WAR at $1.5M generates far more roster flexibility than one producing similar results at $12M. Because undervaluation is first defined by skill misalignment before financial misalignment, SEI does not carry the highest weight. However, it is an essential component in converting skill-based findings into actionable contract decisions.

### 3.6 Stuff Quality Index (SQI) — Weight: 10%

**Formula:** `SQI = Velocity − Hard Hit% − Barrel%`

The SQI captures raw stuff: how well a pitcher's arsenal suppresses hard contact. Fastball velocity is a leading indicator of ceiling, while hard hit rate and barrel rate measure outcomes on contact. The SQI receives the lowest weight because its information is partially redundant with the RPSI and DI — high-velocity pitchers with good stuff typically post strong strikeout and expected run prevention metrics. The SQI functions primarily as a reinforcement signal rather than an independent driver.

---

## 4. Normalization and Composite Scoring

For each index, raw values are rescaled to a 0–100 range using min-max normalization across the full sample:

```
Normalized score = (raw − min) / (max − min) × 100
```

For the RPSI, normalization is inverted since lower values indicate better performance:

```
Normalized RPSI = 100 − [(raw − min) / (max − min) × 100]
```

This approach places all six indices on a common scale where 100 represents the best-performing pitcher in that dimension and 0 represents the worst. Crucially, because all indices are already on a 0–100 range prior to weighting, z-score standardization is unnecessary. The normalization step alone eliminates unit bias and variance differences across metrics.

The final UPS is computed as a weighted sum:

```
UPS = 0.25(RPSI) + 0.20(DI) + 0.15(CCI) + 0.15(LAI) + 0.15(SEI) + 0.10(SQI)
```

---

## 5. Weight Rationale and Design Philosophy

The weighting structure reflects a deliberate hierarchy: predictive skill indicators are prioritized first, regression signals second, and financial inefficiency third.

| Index | Weight | Rationale |
|-------|--------|-----------|
| RPSI  | 25%    | Most predictive of future run prevention; removes defensive and sequencing noise |
| DI    | 20%    | Strikeout metrics stabilize quickly and translate well year-over-year |
| CCI   | 15%    | Walk suppression reduces volatility independent of strikeout ability |
| LAI   | 15%    | Identifies surface-result distortion; diagnostic signal for regression candidates |
| SEI   | 15%    | Converts skill findings into contract and roster value decisions |
| SQI   | 10%    | Reinforcing signal; largely captured by RPSI and DI |

The sum of weights equals 1.0, ensuring UPS values remain on a 0–100 interpretable scale.

---

## 6. Front Office Applications

### 6.1 Buy-Low Identification

A pitcher with a high UPS but an ERA significantly above their xERA is a canonical buy-low candidate. Their surface-level results have been suppressed by unfavorable BABIP, low LOB%, or a large ERA−xERA gap, while the underlying skill profile remains intact. These pitchers represent acquisition targets at potentially reduced cost relative to their true value.

**Example signal:** A starter with a 4.40 ERA, 3.10 xERA, 28% K%, 7% BB%, and a .330 BABIP is performing well below expected results. Their high DI and RPSI combined with a positive LAI produces a strong UPS despite a surface ERA that may discourage competing bids.

### 6.2 Sell-High Identification

A pitcher with a low UPS but a strong ERA is likely outperforming their underlying indicators. Low RPSI (high xERA, FIP, SIERA) combined with a negative LAI (low BABIP, high LOB%) signals that current results are not sustainable. These pitchers represent trade or extension candidates where current value may exceed forward value.

**Example signal:** A reliever posting a 2.60 ERA with a 4.10 FIP, .240 BABIP, and 85% LOB% is almost certainly benefiting from variance. The model's negative LAI and weak RPSI would produce a low UPS, flagging the pitcher as a potential overvaluation.

### 6.3 Contract and Extension Evaluation

The SEI directly addresses whether a pitcher's salary aligns with their production. A pitcher generating 3.0 WAR at $2M ($9M/WAR value at market rate implies ~$27M of value) represents extreme surplus. This framework can be applied to arbitration-eligible pitchers, extension candidates, and free-agent targets to evaluate cost efficiency alongside skill.

### 6.4 Roster Construction

Because the model covers both starters and relievers with role-appropriate sample thresholds, it can support full pitching staff construction decisions. Identifying undervalued relievers at low AAV frees budget flexibility for larger acquisitions. The framework's separation of starters and relievers also respects the distinct performance profiles of each role.

---

## 7. Model Limitations and Considerations

**Sample size constraints:** The 80-inning threshold for starters and 30-inning threshold for relievers are minimum floors. Pitchers near these thresholds have smaller samples and higher performance variance. Rankings should be interpreted with greater caution for pitchers at the threshold boundary.

**Velocity and stuff data:** The SQI relies on average fastball velocity and contact suppression metrics. These do not capture pitch mix complexity, spin rates, or movement profiles that increasingly drive modern pitcher evaluation. Future iterations could incorporate pitch-level Statcast data.

**Injury and availability:** The model evaluates 2025 season performance as given. Pitchers who missed significant time due to injury may have compressed samples that inflate or suppress index values. Context for absence and historical performance trends should supplement model output.

**Multicollinearity across indices:** K%, K-BB%, and BB% are not independent variables. The DI and CCI share walk-rate information. This is a deliberate design choice — the indices are weighted separately because each captures a distinct dimension of performance, even where overlap exists. However, users should be aware that pitchers with strong command will receive reinforced scores across multiple components.

**Salary data completeness:** Pitchers without public salary records default to the league minimum. This overstates SEI for underpaid veterans and understates it for pre-arb pitchers on incentive-heavy deals. Salary matching accuracy degrades for international free agents and players with complex contract structures.

---

## 8. Interpreting UPS Rankings

| UPS Range | Interpretation |
|-----------|---------------|
| 70–100    | Elite underlying profile: strong across most indices |
| 55–69     | Above-average performer; likely above-market value |
| 40–54     | League-average underlying skill |
| 25–39     | Below-average profile; may be overvalued by surface ERA |
| 0–24      | Weak across multiple dimensions; highest regression risk |

A high UPS with a high ERA = buy-low candidate.  
A high UPS with a low ERA = confirmed elite performer.  
A low UPS with a low ERA = sell-high or regression risk candidate.  
A low UPS with a high ERA = likely replacement-level pitcher.

---

## 9. Conclusion

The Undervalued Pitcher Score provides a structured, interpretable framework for evaluating MLB pitchers beyond traditional statistics. By combining defense-independent run prevention estimators, strikeout and walk-rate metrics, luck adjustment signals, and salary efficiency into a single weighted composite, the model translates advanced analytics into actionable roster and contract decisions.

The primary goal is not simply to rank pitchers by historical performance, but to identify discrepancies between surface results and underlying skill that create market inefficiencies. When applied alongside scouting evaluations, health status, and organizational fit, the UPS provides a systematic starting point for buy-low acquisitions, sell-high timing, extension negotiations, and full pitching staff construction.

The framework is deliberately kept interpretable so findings can be communicated across departments — from analysts running the model to executives and coaches making final decisions. Every component maps to a specific, explainable question about pitcher performance, ensuring that the model's output can be defended, challenged, and refined as new data and organizational priorities evolve.

---

## Appendix: Full Formula Reference

| Index | Formula | Direction |
|-------|---------|-----------|
| RPSI  | (xERA + FIP + SIERA) / 3 | Lower = better (inverted in normalization) |
| DI    | 0.6 × (K−BB%) + 0.4 × (K%) | Higher = better |
| CCI   | 100 − BB% | Higher = better |
| LAI   | (ERA − xERA) + (BABIP − .290) + (LOB% − 72.0) | Higher = better (positive = unlucky) |
| SEI   | WAR / Salary (millions) | Higher = better |
| SQI   | Velocity − Hard Hit% − Barrel% | Higher = better |

**Final Score:**
```
UPS = 0.25(RPSI_norm) + 0.20(DI_norm) + 0.15(CCI_norm) + 0.15(LAI_norm) + 0.15(SEI_norm) + 0.10(SQI_norm)
```

All normalized values are on a 0–100 scale where 100 = best in sample and 0 = worst in sample.

---

*Data sources: FanGraphs (via pybaseball), Spotrac (salary data), Baseball Savant (Statcast). Dashboard available at: https://2025-mlb-undervalued-pitchers.vercel.app*
