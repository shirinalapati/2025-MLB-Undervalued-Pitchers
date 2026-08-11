import React, { useState, useMemo, useEffect } from 'react'
import type { PitcherData } from '../types'
import { pitcherMatchesTeam } from '../utils/teams'
import PitcherCard from './PitcherCard'
import './Leaderboard.css'

type SortKey =
  | 'rank'
  | 'name'
  | 'team'
  | 'role'
  | 'IP'
  | 'ERA'
  | 'WAR'
  | 'salary'
  | 'UPS'
  | 'adjusted_UPS'
  | 'reliability_pct'
  | 'SV'
  | 'HLD'
  | 'H'
  | 'ER'
  | 'HR'
  | 'K9'
  | 'WHIP'
  | 'W'
  | 'L'
  | 'K'
  | 'BB'
  | 'K_pct'
  | 'BB_pct'
  | 'xERA'
  | 'FIP'
  | 'SIERA'
  | 'fb_velo'
  | 'hardhit_pct'
  | 'barrel_pct'
  | 'BABIP'
  | 'LOB_pct'
type SortDir = 'asc' | 'desc'

interface LeaderboardProps {
  pitchers: PitcherData[]
  showUPSColumn?: boolean
  showTraditionalStats?: boolean
  isLiveSeason?: boolean
}

/** Get stat from top-level or components for display/sort. */
function getStat(p: PitcherData, key: string): number | string | undefined {
  const rec = p as unknown as Record<string, unknown>
  const top = rec[key]
  if (top !== undefined && top !== null) return top as number | string
  const comp = p.components as Record<string, unknown>
  if (key === 'fb_velo') return comp?.Velo as number | string | undefined
  if (key === 'hardhit_pct') return comp?.HardHit_pct as number | string | undefined
  if (key === 'barrel_pct') return comp?.Barrel_pct as number | string | undefined
  const cv = comp?.[key]
  return cv !== undefined && cv !== null ? (cv as number | string) : undefined
}

/** 30 MLB team abbreviations only (no slash combos like ARI/TEX) */
const MLB_TEAMS = [
  'ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET',
  'HOU', 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'ATH',
  'PHI', 'PIT', 'SDP', 'SEA', 'SFG', 'STL', 'TBR', 'TEX', 'TOR', 'WSN',
]

/** 5 columns for UPS Leaderboard tab only */
const UPS_LEADERBOARD_COLUMNS_LIVE: {
  key: SortKey
  label: string
  filterable?: 'text' | 'number' | 'select'
  filterMode?: 'min' | 'max'
}[] = [
  { key: 'rank', label: 'Rank', filterable: 'number', filterMode: 'max' },
  { key: 'name', label: 'Name', filterable: 'text' },
  { key: 'team', label: 'Team', filterable: 'select' },
  { key: 'role', label: 'Role' },
  { key: 'IP', label: 'IP', filterable: 'number', filterMode: 'min' },
  { key: 'adjusted_UPS', label: 'Adj. UPS', filterable: 'number', filterMode: 'min' },
  { key: 'UPS', label: 'Raw UPS', filterable: 'number', filterMode: 'min' },
  { key: 'reliability_pct', label: 'Reliability %', filterable: 'number', filterMode: 'min' },
]

const UPS_LEADERBOARD_COLUMNS: {
  key: SortKey
  label: string
  filterable?: 'text' | 'number' | 'select'
  filterMode?: 'min' | 'max'
}[] = [
  { key: 'rank', label: 'Rank', filterable: 'number', filterMode: 'max' },
  { key: 'name', label: 'Name', filterable: 'text' },
  { key: 'team', label: 'Team', filterable: 'select' },
  { key: 'role', label: 'Role' },
  { key: 'UPS', label: 'UPS', filterable: 'number', filterMode: 'min' },
]

const ALL_COLUMNS: {
  key: SortKey
  label: string
  filterable?: 'text' | 'number' | 'select'
  filterMode?: 'min' | 'max'
  format?: (v: number) => string
  includeWhenUPSHidden?: boolean
}[] = [
  { key: 'rank', label: 'Rank', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: false },
  { key: 'name', label: 'Player', filterable: 'text', includeWhenUPSHidden: true },
  { key: 'team', label: 'Team', filterable: 'select', includeWhenUPSHidden: true },
  { key: 'role', label: 'Role', includeWhenUPSHidden: true },
  { key: 'IP', label: 'IP', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'ERA', label: 'ERA', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'WAR', label: 'WAR', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'salary', label: 'Salary', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'UPS', label: 'UPS', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: false },
  { key: 'SV', label: 'Saves', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'HLD', label: 'Holds', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'H', label: 'Hits', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'ER', label: 'ER', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'HR', label: 'HR', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'K9', label: 'K/9', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'WHIP', label: 'WHIP', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'W', label: 'W', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'L', label: 'L', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'K', label: 'K', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'BB', label: 'BB', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'K_pct', label: 'K%', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'BB_pct', label: 'BB%', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'xERA', label: 'xERA', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'FIP', label: 'FIP', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'SIERA', label: 'SIERA', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'fb_velo', label: 'FB Velo', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
  { key: 'hardhit_pct', label: 'Hard Hit%', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'barrel_pct', label: 'Barrel%', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'BABIP', label: 'BABIP', filterable: 'number', filterMode: 'max', includeWhenUPSHidden: true },
  { key: 'LOB_pct', label: 'LOB%', filterable: 'number', filterMode: 'min', includeWhenUPSHidden: true },
]

function lastName(p: PitcherData): string {
  const parts = p.name.trim().split(/\s+/)
  return parts.length > 1 ? parts[parts.length - 1] : p.name
}

function Leaderboard({ pitchers, showUPSColumn = true, showTraditionalStats = false, isLiveSeason = false }: LeaderboardProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const defaultSort: SortKey = showUPSColumn ? (isLiveSeason ? 'adjusted_UPS' : 'UPS') : 'name'
  const [sortKey, setSortKey] = useState<SortKey>(defaultSort)
  const [sortDir, setSortDir] = useState<SortDir>(showUPSColumn ? 'desc' : 'asc')
  const [filters, setFilters] = useState<Record<string, string>>({})

  const COLUMNS = useMemo(
    () =>
      showUPSColumn
        ? isLiveSeason
          ? UPS_LEADERBOARD_COLUMNS_LIVE
          : UPS_LEADERBOARD_COLUMNS
        : ALL_COLUMNS.filter((c) => c.includeWhenUPSHidden !== false),
    [showUPSColumn, isLiveSeason]
  )

  useEffect(() => {
    if (showUPSColumn) {
      setSortKey(isLiveSeason ? 'adjusted_UPS' : 'UPS')
      setSortDir('desc')
    } else {
      setSortKey('name')
      setSortDir('asc')
    }
  }, [showUPSColumn, isLiveSeason])

  const formatSalary = (n: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(n)

  const teamFilterOptions = MLB_TEAMS

  const filteredAndSorted = useMemo(() => {
    let list = [...pitchers]

    COLUMNS.forEach((col) => {
      const val = filters[col.key]?.trim()
      if (!val) return

      if (col.filterable === 'text') {
        list = list.filter((p) =>
          String((p as unknown as Record<string, unknown>)[col.key])
            .toLowerCase()
            .includes(val.toLowerCase())
        )
      } else if (col.filterable === 'select') {
        if (col.key === 'team') {
          list = list.filter((p) => pitcherMatchesTeam(p.team, val))
        } else {
          list = list.filter(
            (p) => String((p as unknown as Record<string, unknown>)[col.key]).toLowerCase() === val.toLowerCase()
          )
        }
      } else if (col.filterable === 'number') {
        const num = parseFloat(val)
        if (!isNaN(num)) {
          const mode = col.filterMode ?? 'min'
          list = list.filter((p) => {
            const v = getStat(p, col.key)
            const n = typeof v === 'number' ? v : parseFloat(String(v))
            if (isNaN(n)) return false
            return mode === 'min' ? n >= num : n <= num
          })
        }
      }
    })

    list.sort((a, b) => {
      // Sort by last name when sortKey is 'name'
      if (sortKey === 'name') {
        const cmp = lastName(a).localeCompare(lastName(b), undefined, { sensitivity: 'base' })
        return sortDir === 'asc' ? cmp : -cmp
      }
      const ak = getStat(a, sortKey) ?? (a as unknown as Record<string, unknown>)[sortKey]
      const bk = getStat(b, sortKey) ?? (b as unknown as Record<string, unknown>)[sortKey]
      let cmp = 0
      if (typeof ak === 'number' && typeof bk === 'number') {
        cmp = ak - bk
      } else if (typeof ak === 'string' && typeof bk === 'string') {
        cmp = ak.localeCompare(bk)
      } else {
        cmp = String(ak ?? '').localeCompare(String(bk ?? ''))
      }
      return sortDir === 'asc' ? cmp : -cmp
    })

    return list
  }, [pitchers, filters, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const updateFilter = (key: string, value: string) => {
    setFilters((f) => ({ ...f, [key]: value }))
  }

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <h2>{showUPSColumn ? 'UPS Leaderboard' : 'Pitcher Stats'}</h2>
        {showUPSColumn && (
          <div className="ups-formulas">
            <p className="ups-formula">UPS = 0.2(DI) + 0.15(CCI) + 0.25(RPSI) + 0.1(SQI) + 0.15(LAI) + 0.15(SEI)</p>
            {isLiveSeason && (
              <p className="formula-note">
                Raw UPS and index scores refresh with Statcast (~4× daily). Counting stats (IP, ERA, K, BB) update
                more often via the MLB API; Reliability % and Adj. UPS can shift between Statcast runs as IP changes.
              </p>
            )}
            {isLiveSeason && (
              <p className="index-formula">Adj. UPS = reliability × UPS + (1 − reliability) × 50, where reliability = IP / (IP + k)</p>
            )}
            <p className="index-formula">Dominance Index (DI) = 0.6(K-BB%) + 0.4(K%)</p>
            <p className="index-formula">Command &amp; Control Index (CCI) = 100 − BB%</p>
            <p className="index-formula">Run Prevention Skill Index (RPSI) = 1/3(xERA + FIP + SIERA)</p>
            <p className="index-formula">Stuff Quality Index (SQI) = Velocity − HardHit% − Barrel%</p>
            <p className="index-formula">Luck Adjustment Index (LAI) = (ERA−xERA)+(BABIP−LeagueBABIP)+(LOB%−LeagueLOB%)</p>
            <p className="index-formula">Salary Efficiency Index (SEI) = WAR/Salary_Millions</p>
          </div>
        )}
      </div>

      <div className="table-wrapper">
        <table className="leaderboard-table">
          <thead>
            <tr className="filter-row">
              {COLUMNS.map((col) => (
                <th key={col.key}>
                  {col.filterable === 'text' && (
                    <input
                      type="text"
                      placeholder={`Filter ${col.label}`}
                      value={filters[col.key] ?? ''}
                      onChange={(e) => updateFilter(col.key, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="filter-input"
                    />
                  )}
                  {col.filterable === 'select' && col.key === 'team' && (
                    <select
                      value={filters[col.key] ?? ''}
                      onChange={(e) => updateFilter(col.key, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="filter-select"
                    >
                      <option value="">All {col.label}</option>
                      {teamFilterOptions.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  )}
                  {col.filterable === 'number' && (
                    <input
                      type="number"
                      placeholder={(col.filterMode ?? 'min') === 'min' ? `Min ${col.label}` : `Max ${col.label}`}
                      value={filters[col.key] ?? ''}
                      onChange={(e) => updateFilter(col.key, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="filter-input filter-number"
                    />
                  )}
                  {!col.filterable && <span />}
                </th>
              ))}
              <th />
            </tr>
            <tr className="header-row">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="sortable"
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="sort-icon">{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
                  )}
                </th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.map((p, idx) => (
              <React.Fragment key={`${p.name}-${p.team}-${idx}`}>
                <tr
                  className={`row-main ${expandedId === p.rank ? 'expanded' : ''} ${isLiveSeason && p.low_sample ? 'low-sample' : ''}`}
                  onClick={() => setExpandedId(expandedId === p.rank ? null : p.rank)}
                >
                  {COLUMNS.map((col) => {
                    const v = getStat(p, col.key)
                    const raw = (p as unknown as Record<string, unknown>)[col.key]
                    const displayVal: unknown = col.key === 'rank' ? p.rank : col.key === 'name' ? p.name : col.key === 'team' ? p.team : col.key === 'salary' ? formatSalary(p.salary) : v ?? raw
                    const num = typeof displayVal === 'number' ? displayVal : parseFloat(String(displayVal))
                    const isUpsCol = col.key === 'UPS' || col.key === 'adjusted_UPS'
                    const isIpCol = col.key === 'IP'
                    return (
                      <td
                        key={col.key}
                        className={[
                          col.key === 'name' ? 'name' : '',
                          isLiveSeason && p.low_sample && isIpCol ? 'low-sample-ip' : '',
                        ].filter(Boolean).join(' ')}
                      >
                        {col.key === 'name' ? (
                          String(displayVal ?? '')
                        ) : col.key === 'team' ? (
                          String(displayVal ?? '')
                        ) : col.key === 'salary' ? (
                          typeof p.salary === 'number' && !Number.isNaN(p.salary) ? formatSalary(p.salary) : '—'
                        ) : col.key === 'role' ? (
                          <span className={`badge ${displayVal}`}>{String(displayVal ?? '')}</span>
                        ) : isUpsCol ? (
                          <strong className="ups-value">{typeof displayVal === 'number' ? (displayVal as number).toFixed(1) : String(displayVal ?? '')}</strong>
                        ) : displayVal === undefined || displayVal === null ? (
                          '—'
                        ) : col.key === 'BABIP' ? (
                          num.toFixed(3)
                        ) : col.key === 'fb_velo' ? (
                          `${num} mph`
                        ) : ['K_pct', 'BB_pct', 'hardhit_pct', 'barrel_pct', 'LOB_pct', 'reliability_pct'].includes(col.key) ? (
                          `${num}%`
                        ) : col.key === 'ERA' || col.key === 'WAR' ? (
                          typeof displayVal === 'number' ? (displayVal as number).toFixed(2) : String(displayVal)
                        ) : Number.isInteger(num) && !Number.isNaN(num) ? (
                          String(num)
                        ) : !Number.isNaN(num) ? (
                          num.toFixed(2)
                        ) : (
                          String(displayVal ?? '—')
                        )}
                      </td>
                    )
                  })}
                  <td>
                    <span className="expand-icon">{expandedId === p.rank ? '−' : '+'}</span>
                  </td>
                </tr>
                {expandedId === p.rank && (
                  <tr className="row-detail">
                    <td colSpan={COLUMNS.length + 2}>
                      <PitcherCard pitcher={p} showTraditionalStats={showTraditionalStats} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <p className="result-count">
        Showing {filteredAndSorted.length} of {pitchers.length} pitchers
      </p>
    </div>
  )
}

export default Leaderboard
