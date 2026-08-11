/** Match pitcher team field to a filter abbreviation (2025 abbrevs + 2026 full names). */

const ABBR_ALIASES: Record<string, string[]> = {
  ARI: ['ARI', 'Arizona', 'Arizona Diamondbacks'],
  ATH: ['ATH', 'OAK', 'Athletics', 'Oakland Athletics'],
  ATL: ['ATL', 'Atlanta', 'Atlanta Braves'],
  BAL: ['BAL', 'Baltimore', 'Baltimore Orioles'],
  BOS: ['BOS', 'Boston', 'Boston Red Sox'],
  CHC: ['CHC', 'Chicago Cubs'],
  CHW: ['CHW', 'Chicago White Sox'],
  CIN: ['CIN', 'Cincinnati', 'Cincinnati Reds'],
  CLE: ['CLE', 'Cleveland', 'Cleveland Guardians'],
  COL: ['COL', 'Colorado', 'Colorado Rockies'],
  DET: ['DET', 'Detroit', 'Detroit Tigers'],
  HOU: ['HOU', 'Houston', 'Houston Astros'],
  KCR: ['KCR', 'KC', 'Kansas City', 'Kansas City Royals'],
  LAA: ['LAA', 'Los Angeles Angels', 'Anaheim'],
  LAD: ['LAD', 'Los Angeles Dodgers'],
  MIA: ['MIA', 'Miami', 'Miami Marlins'],
  MIL: ['MIL', 'Milwaukee', 'Milwaukee Brewers'],
  MIN: ['MIN', 'Minnesota', 'Minnesota Twins'],
  NYM: ['NYM', 'New York Mets'],
  NYY: ['NYY', 'New York Yankees'],
  PHI: ['PHI', 'Philadelphia', 'Philadelphia Phillies'],
  PIT: ['PIT', 'Pittsburgh', 'Pittsburgh Pirates'],
  SDP: ['SDP', 'SD', 'San Diego', 'San Diego Padres'],
  SEA: ['SEA', 'Seattle', 'Seattle Mariners'],
  SFG: ['SFG', 'SF', 'San Francisco', 'San Francisco Giants'],
  STL: ['STL', 'St. Louis', 'St. Louis Cardinals'],
  TBR: ['TBR', 'TB', 'Tampa Bay', 'Tampa Bay Rays'],
  TEX: ['TEX', 'Texas', 'Texas Rangers'],
  TOR: ['TOR', 'Toronto', 'Toronto Blue Jays'],
  WSN: ['WSN', 'WSH', 'Washington', 'Washington Nationals'],
}

function normalizeToken(token: string): string {
  return token.trim().toLowerCase()
}

/** True if pitcher team string (e.g. SFG, San Francisco, MIN/TBR) matches filter abbr. */
export function pitcherMatchesTeam(pitcherTeam: string, filterAbbr: string): boolean {
  const aliases = ABBR_ALIASES[filterAbbr.toUpperCase()]
  if (!aliases) {
    return pitcherTeam.split(/[,/]/).some((t) => normalizeToken(t) === normalizeToken(filterAbbr))
  }
  const aliasSet = new Set(aliases.map(normalizeToken))
  return pitcherTeam.split(/[,/]/).some((t) => aliasSet.has(normalizeToken(t.trim())))
}
