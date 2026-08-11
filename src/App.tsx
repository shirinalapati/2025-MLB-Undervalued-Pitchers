import { useState, useEffect, useCallback } from 'react'
import type { PitcherData } from './types'
import Leaderboard from './components/Leaderboard'
import AboutPage from './components/AboutPage'
import './App.css'

type TabId = 'about' | 'all' | 'starters' | 'relievers' | 'leaderboard'
type SeasonMode = '2025' | '2026'

interface SeasonMeta {
  full_updated?: string
  mlb_live_updated?: string
  low_sample_threshold_starter?: number
  low_sample_threshold_reliever?: number
  pitcher_count?: number
}

const POLL_MS = 2 * 60 * 1000

/** Bypass CDN/browser cache so GitHub Actions JSON commits show up on poll. */
function fetchLiveAsset(path: string) {
  return fetch(`${path}?v=${Date.now()}`, { cache: 'no-store' })
}

function App() {
  const [season, setSeason] = useState<SeasonMode>('2026')
  const [pitchers, setPitchers] = useState<PitcherData[]>([])
  const [meta, setMeta] = useState<SeasonMeta | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('about')
  const [leaderboardRoleFilter, setLeaderboardRoleFilter] = useState<'all' | 'starter' | 'reliever'>('all')
  const [showGlossary, setShowGlossary] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const loadSeason = useCallback(async (mode: SeasonMode, quiet = false) => {
    if (!quiet) {
      setLoading(true)
      setError(null)
    }
    const dataPath = mode === '2025' ? '/data/pitchers_2025.json' : '/data/pitchers_2026.json'
    try {
      const [dataRes, metaRes, tsRes, liveTsRes] = await Promise.all([
        fetchLiveAsset(dataPath),
        mode === '2026' ? fetchLiveAsset('/data/pitchers_2026_meta.json') : Promise.resolve(null),
        mode === '2026' ? fetchLiveAsset('/data/last_updated_2026.txt') : Promise.resolve(null),
        mode === '2026' ? fetchLiveAsset('/data/last_updated_mlb_live_2026.txt') : Promise.resolve(null),
      ])
      if (!dataRes.ok) {
        throw new Error(
          mode === '2026'
            ? '2026 data not found. Run: python scripts/fetch_2026_pitcher_data.py'
            : '2025 data not found. Run: npm run data'
        )
      }
      const data = (await dataRes.json()) as PitcherData[]
      setPitchers(data)

      if (mode === '2026') {
        let nextMeta: SeasonMeta = {}
        if (metaRes?.ok) {
          nextMeta = (await metaRes.json()) as SeasonMeta
        }
        if (tsRes?.ok) {
          nextMeta.full_updated = (await tsRes.text()).trim()
        }
        if (liveTsRes?.ok) {
          nextMeta.mlb_live_updated = (await liveTsRes.text()).trim()
        }
        setMeta(nextMeta)
      } else {
        setMeta(null)
      }
    } catch (e) {
      if (!quiet) {
        setError(e instanceof Error ? e.message : 'Failed to load data')
        setPitchers([])
      }
    } finally {
      if (!quiet) setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSeason(season)
  }, [season, loadSeason])

  useEffect(() => {
    if (season !== '2026') return
    const id = window.setInterval(() => loadSeason('2026', true), POLL_MS)
    return () => window.clearInterval(id)
  }, [season, loadSeason])

  const is2026 = season === '2026'
  const isAboutTab = activeTab === 'about'
  const isLeaderboardTab = activeTab === 'leaderboard'

  const searchFiltered = searchQuery.trim()
    ? pitchers.filter((p) => p.name.toLowerCase().includes(searchQuery.trim().toLowerCase()))
    : pitchers

  const filtered = isLeaderboardTab
    ? searchFiltered.filter((p) =>
        leaderboardRoleFilter === 'all' ? true : p.role === leaderboardRoleFilter
      )
    : searchFiltered.filter((p) =>
        activeTab === 'all' ? true : p.role === (activeTab === 'starters' ? 'starter' : 'reliever')
      )

  const showUPSColumn = isLeaderboardTab
  const title = is2026 ? '2026 MLB Undervalued Pitchers (Live)' : '2025 MLB Undervalued Pitchers Analysis'
  const subtitle = is2026
    ? 'Live 2026 season: all pitchers with Statcast data. Leaderboard sorted by reliability-adjusted UPS; yellow rows flag low sample size.'
    : '2025 regular season: Basic and advanced statistics for all starters with at least 80 innings and relievers with at least 30 innings pitched'

  return (
    <div className="app">
      <header className="app-header">
        <h1>{title}</h1>
        <p className="subtitle">{subtitle}</p>

        <div className="season-controls">
          <label htmlFor="season-select">Season</label>
          <select
            id="season-select"
            value={season}
            onChange={(e) => setSeason(e.target.value as SeasonMode)}
          >
            <option value="2025">2025 Full Season</option>
            <option value="2026">2026 Live Season</option>
          </select>
          {!isAboutTab && (
            <input
              type="search"
              className="player-search"
              placeholder="Search pitcher…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search pitcher by name"
            />
          )}
        </div>

        {is2026 && !isAboutTab && meta && (
          <div className="live-timestamps">
            {meta.mlb_live_updated && (
              <span>Counting stats (IP, ERA, K, BB): <strong>{meta.mlb_live_updated}</strong></span>
            )}
            {meta.full_updated && (
              <span>UPS / advanced stats (xERA, barrel%, WAR): <strong>{meta.full_updated}</strong></span>
            )}
          </div>
        )}

        {is2026 && !isAboutTab && (
          <div className="refresh-data-notice">
            <strong>How updates work — </strong>
            UPS uses mostly advanced metrics (xERA, FIP, SIERA, barrel%, hard-hit%, WAR), so{' '}
            <strong>Raw UPS and Adj. UPS fully refresh only when Statcast data updates</strong>{' '}
            (see second timestamp above, roughly 4× per day). Between those runs, the MLB API refresh
            updates IP, ERA, strikeouts, and walks more often — which moves{' '}
            <strong>Reliability %</strong> and can shift <strong>Adj. UPS</strong> as innings accumulate,
            but Raw UPS stays fixed until the next Statcast pull.
          </div>
        )}

        {is2026 && !isAboutTab && (
          <div className="sample-size-notice">
            <strong>Sample size caution — </strong>
            The 2026 view includes every pitcher with Statcast data (no IP minimum).
            Rows highlighted in <strong>yellow</strong> are below the current low-sample cutoff
            {meta?.low_sample_threshold_starter != null && (
              <>
                {' '}(starters &lt; {meta.low_sample_threshold_starter} IP, relievers &lt;{' '}
                {meta.low_sample_threshold_reliever} IP — about 35% of league median).
              </>
            )}
            {' '}Always check <strong>IP</strong> before drawing conclusions.
          </div>
        )}

        <button
          type="button"
          className="glossary-toggle"
          onClick={() => setShowGlossary((v) => !v)}
          aria-expanded={showGlossary}
        >
          {showGlossary ? 'Hide Metrics Glossary' : 'Show Metrics Glossary'}
        </button>
        {showGlossary && (
          <section className="glossary-panel" aria-label="Metrics Glossary">
            <dl>
              <dt>IP</dt>
              <dd>Innings Pitched</dd>
              <dt>ERA</dt>
              <dd>Average number of earned runs allowed per 9 innings pitched</dd>
              <dt>WAR (Wins Above Replacement)</dt>
              <dd>An estimate of the number of wins a pitcher adds compared to a replacement-level player. Incorporates run prevention, innings pitched, and context adjustments.</dd>
              <dt>Salary</dt>
              <dd>The amount of money the pitcher was making in 2025. Used to evaluate cost efficiency and surplus value.</dd>
              <dt>Saves</dt>
              <dd>Awarded to a relief pitcher typically who finishes a game for the winning team under qualifying high-leverage conditions (usually protecting a lead of 3 runs or fewer)</dd>
              <dt>Holds</dt>
              <dd>Credited to a relief pitcher who enters in a save situation, records at least one out, and maintains the lead without finishing the game.</dd>
              <dt>Hits (H)</dt>
              <dd>Total number of hits allowed</dd>
              <dt>ER (Earned Runs)</dt>
              <dd>Runs scored against the pitcher that aren&apos;t the result of fielding errors or passed balls</dd>
              <dt>HR</dt>
              <dd>Home Runs allowed</dd>
              <dt>K/9</dt>
              <dd>Average number of strikeouts recorded per 9 innings pitched</dd>
              <dt>WHIP (Walks + Hits per Inning Pitched)</dt>
              <dd>Average number of baserunners allowed per inning</dd>
              <dt>W (Wins)</dt>
              <dd>Credited to a pitcher when they are the pitcher of record at the time their team takes a lead it does not relinquish. A starter must pitch at least 5 full innings in a 9-inning game and leave with the lead, and the team must never lose that lead for the rest of the game. Relievers get wins if they are on the mound when their team takes a permanent lead.</dd>
              <dt>L (Losses)</dt>
              <dd>Assigned to the pitcher responsible for the go-ahead run in a loss</dd>
              <dt>K (Strikeouts)</dt>
              <dd>Total strikeouts</dd>
              <dt>BB (Walks)</dt>
              <dd>Total walks allowed</dd>
              <dt>K% (Strikeout Rate)</dt>
              <dd>Percentage of batters faced who struck out</dd>
              <dt>BB% (Walk Rate)</dt>
              <dd>Percentage of batters faced who walk</dd>
              <dt>xERA (Expected ERA)</dt>
              <dd>Statcast-based estimate of ERA derived from strikeouts, walks, and quality of contact. It removes sequencing luck and defensive effect.</dd>
              <dt>FIP (Fielding Independent Pitching)</dt>
              <dd>Estimates ERA based only on events a pitcher directly controls like strikeouts, walks, hit batters, and home runs. Any defensive influence is removed.</dd>
              <dt>SIERA (Skill-Interactive ERA)</dt>
              <dd>An advanced run estimator that accounts for strikeouts, walks, and batted-ball tendencies. Usually considered more predictive than ERA or FIP.</dd>
              <dt>FB Velo (Fastball Velocity)</dt>
              <dd>Average velocity (mph) of the pitcher&apos;s primary fastball.</dd>
              <dt>Hard Hit%</dt>
              <dd>Percentage of batted balls hit at 95+ mph exit velocity. Lower values indicate weaker contact allowed</dd>
              <dt>Barrel%</dt>
              <dd>Percentage of batted balls classified as &quot;barrels&quot; which is best described as an optimal combination of exit velocity and launch angle. Strong indicator of damaging contact allowed</dd>
              <dt>BABIP (Batting Average on Balls in Play)</dt>
              <dd>Average allowed on non-home-run balls put in play</dd>
              <dt>LOB% (Left-On-Base Percentage/Strand Rate)</dt>
              <dd>Percentage of baserunners stranded (not allowed to score). Extremely high or low values often regress toward league average</dd>
              {is2026 && (
                <>
                  <dt>Adj. UPS</dt>
                  <dd>Reliability-adjusted Undervalued Pitcher Score. Regresses UPS toward 50 for pitchers with fewer innings, so early-season small samples don&apos;t dominate the leaderboard.</dd>
                  <dt>Reliability %</dt>
                  <dd>Weight given to raw UPS based on innings pitched (higher IP = more weight on observed UPS).</dd>
                </>
              )}
            </dl>
          </section>
        )}
        <div className="filters">
          <button
            className={activeTab === 'about' ? 'active' : ''}
            onClick={() => setActiveTab('about')}
          >
            About This Page
          </button>
          <button
            className={activeTab === 'all' ? 'active' : ''}
            onClick={() => setActiveTab('all')}
          >
            All
          </button>
          <button
            className={activeTab === 'starters' ? 'active' : ''}
            onClick={() => setActiveTab('starters')}
          >
            Starters
          </button>
          <button
            className={activeTab === 'relievers' ? 'active' : ''}
            onClick={() => setActiveTab('relievers')}
          >
            Relievers
          </button>
          <button
            className={activeTab === 'leaderboard' ? 'active' : ''}
            onClick={() => setActiveTab('leaderboard')}
          >
            Undervalued Pitchers Score Leaderboard
          </button>
        </div>
        {isLeaderboardTab && (
          <div className="filters leaderboard-filters">
            <button
              className={leaderboardRoleFilter === 'all' ? 'active' : ''}
              onClick={() => setLeaderboardRoleFilter('all')}
            >
              All
            </button>
            <button
              className={leaderboardRoleFilter === 'starter' ? 'active' : ''}
              onClick={() => setLeaderboardRoleFilter('starter')}
            >
              Starters
            </button>
            <button
              className={leaderboardRoleFilter === 'reliever' ? 'active' : ''}
              onClick={() => setLeaderboardRoleFilter('reliever')}
            >
              Relievers
            </button>
          </div>
        )}
      </header>

      <main className="app-main">
        {isAboutTab && <AboutPage />}
        {!isAboutTab && loading && (
          <div className="loading">
            <div className="spinner" />
            <p>Loading pitcher data...</p>
          </div>
        )}
        {!isAboutTab && error && (
          <div className="error">
            <h2>Data Not Found</h2>
            <p>{error}</p>
            <p className="hint">
              Run <code>python scripts/fetch_{is2026 ? '2026_' : ''}pitcher_data.py</code> to generate the data.
            </p>
          </div>
        )}
        {!isAboutTab && !loading && !error && pitchers.length > 0 && (
          <Leaderboard
            pitchers={filtered}
            showUPSColumn={showUPSColumn}
            showTraditionalStats={false}
            isLiveSeason={is2026}
          />
        )}
        {!isAboutTab && !loading && !error && pitchers.length === 0 && (
          <div className="loading">
            <p>No pitcher data available.</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
