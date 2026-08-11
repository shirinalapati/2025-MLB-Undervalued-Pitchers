export interface PitcherData {
  name: string
  team: string
  role: 'starter' | 'reliever'
  IP: number
  ERA: number
  WAR: number
  salary: number
  rank: number
  UPS: number
  /** MLBAM id — present on 2026 live records */
  player_id?: number
  season?: number
  /** Sample-size-adjusted UPS for 2026 live season */
  adjusted_UPS?: number
  reliability_pct?: number
  low_sample?: boolean
  low_sample_threshold?: number
  /** Raw strikeouts */
  K?: number
  /** Raw walks */
  BB?: number
  /** Strikeout rate */
  K_pct?: number
  /** Walk rate */
  BB_pct?: number
  /** Expected ERA */
  xERA?: number
  /** Fielding Independent Pitching */
  FIP?: number
  /** Skill-Interactive ERA */
  SIERA?: number
  /** Avg fastball velocity (mph) */
  fb_velo?: number
  /** Hard-hit rate */
  hardhit_pct?: number
  /** Barrel rate */
  barrel_pct?: number
  /** Batting avg on balls in play */
  BABIP?: number
  /** Left on base % */
  LOB_pct?: number
  /** Hits allowed */
  H?: number
  /** Earned runs allowed */
  ER?: number
  /** Home runs allowed */
  HR?: number
  /** Saves */
  SV?: number
  /** Holds */
  HLD?: number
  /** Wins */
  W?: number
  /** Losses */
  L?: number
  /** Strikeouts per 9 innings */
  K9?: number
  /** Walks + hits per inning */
  WHIP?: number
  raw: {
    DI: number
    CCI: number
    RPSI: number
    SQI: number
    LAI: number
    SEI: number
  }
  normalized: {
    DI: number
    CCI: number
    RPSI: number
    SQI: number
    LAI: number
    SEI: number
  }
  components: {
    K_pct: number
    BB_pct: number
    K_BB_pct: number
    xERA: number
    FIP: number
    SIERA: number
    Velo: number
    HardHit_pct: number
    Barrel_pct: number
    BABIP: number
    LOB_pct: number
  }
}

export const INDEX_LABELS: Record<string, string> = {
  DI: 'Dominance Index',
  CCI: 'Command & Control Index',
  RPSI: 'Run Prevention Skill Index',
  SQI: 'Stuff Quality Index',
  LAI: 'Luck Adjustment Index',
  SEI: 'Salary Efficiency Index',
}

/** Full descriptions for tooltips — interpretable model documentation */
export const INDEX_DESCRIPTIONS: Record<string, string> = {
  DI: '0.6×(K-BB%) + 0.4×(K%). Strikeout dominance minus walks.',
  CCI: '100 − BB%. Command and control; lower walk rate is better.',
  RPSI: 'avg(xERA, FIP, SIERA). Skill-based run prevention; lower is better.',
  SQI: 'Velo − HardHit% − Barrel%. Raw stuff vs. contact quality allowed.',
  LAI: '(ERA−xERA) + BABIP + LOB vs. league. Separates skill from luck.',
  SEI: 'WAR / Salary_Millions. Value for cost; production relative to AAV.',
}

export const INDEX_WEIGHTS: Record<string, number> = {
  DI: 0.20,
  CCI: 0.15,
  RPSI: 0.25,
  SQI: 0.10,
  LAI: 0.15,
  SEI: 0.15,
}
