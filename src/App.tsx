import { useState, useEffect } from 'react'
import type { PitcherData } from './types'
import Leaderboard from './components/Leaderboard'
import AboutPage from './components/AboutPage'
import './App.css'

type TabId = 'about' | 'all' | 'starters' | 'relievers' | 'leaderboard'

function App() {
  const [pitchers, setPitchers] = useState<PitcherData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('about')
  const [leaderboardRoleFilter, setLeaderboardRoleFilter] = useState<'all' | 'starter' | 'reliever'>('all')
  const [showGlossary, setShowGlossary] = useState(false)

  useEffect(() => {
    fetch('/data/pitchers.json')
      .then((r) => {
        if (!r.ok) throw new Error('Data not found. Run: npm run data')
        return r.json()
      })
      .then(setPitchers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const isAboutTab = activeTab === 'about'
  const isLeaderboardTab = activeTab === 'leaderboard'
  const filtered = isLeaderboardTab
    ? pitchers.filter((p) =>
        leaderboardRoleFilter === 'all' ? true : p.role === leaderboardRoleFilter
      )
    : pitchers.filter((p) =>
        activeTab === 'all' ? true : p.role === (activeTab === 'starters' ? 'starter' : 'reliever')
      )
  const showUPSColumn = isLeaderboardTab

  return (
    <div className="app">
      <header className="app-header">
        <h1>2025 MLB Undervalued Pitchers Analysis</h1>
        <p className="subtitle">
          2025 regular season: Basic and advanced statistics for all starters with at least 80 innings and relievers with at least 30 innings pitched
        </p>
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
              Run <code>python scripts/fetch_pitcher_data.py</code> to generate the data, or place{' '}
              <code>pitchers.json</code> in <code>public/data/</code>.
            </p>
          </div>
        )}
        {!isAboutTab && !loading && !error && pitchers.length > 0 && (
          <Leaderboard
            pitchers={filtered}
            showUPSColumn={showUPSColumn}
            showTraditionalStats={false}
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
