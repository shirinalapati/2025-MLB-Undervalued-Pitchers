import type { PitcherData } from '../types'
import { INDEX_LABELS, INDEX_WEIGHTS, INDEX_DESCRIPTIONS } from '../types'
import './PitcherCard.css'

interface PitcherCardProps {
  pitcher: PitcherData
  showTraditionalStats?: boolean
}

const TRADITIONAL_STATS: { key: keyof PitcherData; label: string }[] = [
  { key: 'SV', label: 'Saves' },
  { key: 'HLD', label: 'Holds' },
  { key: 'H', label: 'Hits' },
  { key: 'ER', label: 'ER' },
  { key: 'HR', label: 'HR Allowed' },
  { key: 'K9', label: 'K/9' },
  { key: 'WHIP', label: 'WHIP' },
  { key: 'W', label: 'W' },
  { key: 'L', label: 'L' },
]

function PitcherCard({ pitcher, showTraditionalStats = false }: PitcherCardProps) {
  const keys = ['DI', 'CCI', 'RPSI', 'SQI', 'LAI', 'SEI'] as const

  return (
    <div className="pitcher-card">
      <h3 className="card-title">{pitcher.name} — All Six Indices</h3>

      {showTraditionalStats && (
        <div className="traditional-stats">
          {TRADITIONAL_STATS.map(({ key, label }) => {
            const val = (pitcher as unknown as Record<string, unknown>)[key]
            return (
              <span key={key} className="traditional-stat">
                <strong>{label}:</strong> {val != null ? String(val) : '—'}
              </span>
            )
          })}
        </div>
      )}

      <div className="indices-grid">
        {keys.map((key) => (
          <div key={key} className="index-block" title={INDEX_DESCRIPTIONS[key]}>
            <div className="index-header">
              <span className="index-name">{INDEX_LABELS[key]}</span>
              <span className="index-weight">{(INDEX_WEIGHTS[key] * 100).toFixed(0)}%</span>
            </div>
            <div className="index-values">
              <div className="value-row">
                <span>Raw:</span>
                <span>{pitcher.raw[key].toFixed(2)}</span>
              </div>
              <div className="value-row">
                <span>Normalized (0–100):</span>
                <span className="norm-value">{pitcher.normalized[key].toFixed(1)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default PitcherCard
