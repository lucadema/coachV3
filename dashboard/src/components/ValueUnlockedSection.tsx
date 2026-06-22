import { useEffect, useMemo, useState } from 'react'
import {
  DEFAULT_HOURLY_RATE,
  calculateValueMetrics,
  cleanHourlyRateInput,
  formatCurrencyGBP,
  formatHours,
  hourlyRateStorageKey,
  parseHourlyRate,
} from '../data/valueCalculations'
import type { DashboardValueInputs } from '../types'
import { MetricCard } from './MetricCard'

type ValueUnlockedSectionProps = {
  tokenKey: string
  valueInputs: DashboardValueInputs
}

export function ValueUnlockedSection({ tokenKey, valueInputs }: ValueUnlockedSectionProps) {
  const storageKey = hourlyRateStorageKey(tokenKey)
  const [hourlyRateInput, setHourlyRateInput] = useState(() =>
    loadSavedHourlyRate(storageKey),
  )
  const hourlyRate = useMemo(() => parseHourlyRate(hourlyRateInput), [hourlyRateInput])
  const metrics = calculateValueMetrics(valueInputs.monthly_minutes, hourlyRate)
  const hasValueResponses = valueInputs.qualifying_responses_count > 0
  const flagYesCount = valueInputs.flag_to_organisation?.yes_count ?? 0
  const flagNoCount = valueInputs.flag_to_organisation?.no_count ?? 0
  const flagTotal = flagYesCount + flagNoCount
  const flagYesPercentage = flagTotal > 0 ? Math.round((flagYesCount / flagTotal) * 100) : 0
  const flagNoPercentage = flagTotal > 0 ? 100 - flagYesPercentage : 0

  useEffect(() => {
    saveHourlyRate(storageKey, hourlyRateInput)
  }, [hourlyRateInput, storageKey])

  function handleHourlyRateChange(value: string) {
    setHourlyRateInput(cleanHourlyRateInput(value))
  }

  return (
    <section className="dashboard-section" aria-labelledby="value-unlocked-title">
      <div className="section-header">
        <div>
          <p className="eyebrow">Section 3</p>
          <h2 id="value-unlocked-title">Value Unlocked</h2>
        </div>
        {hasValueResponses ? (
          <span>{valueInputs.qualifying_responses_count} responses included</span>
        ) : null}
      </div>

      {hasValueResponses ? (
        <>
          <div className="value-grid">
            <MetricCard
              label="Recoverable time"
              suffix="/ month"
              value={`${formatHours(metrics.monthlyHours)} hrs`}
            />
            <MetricCard
              label="Estimated monthly value"
              suffix="/ month"
              value={formatCurrencyGBP(metrics.monthlyValue)}
            />
            <MetricCard
              label="Estimated annual value"
              suffix="/ year"
              value={formatCurrencyGBP(metrics.annualValue)}
            />
            <MetricCard
              label="Feedback responses"
              value={String(valueInputs.qualifying_responses_count)}
            />
          </div>
        </>
      ) : (
        <p className="empty-state">No completed value responses yet.</p>
      )}

      <div className="flag-subsection" aria-labelledby="flag-to-organisation-title">
        <div className="flag-subsection-header">
          <div>
            <h3 id="flag-to-organisation-title">Flagged to organisation</h3>
            <p>Should this be flagged as something worth acting on?</p>
          </div>
          {flagTotal > 0 ? <span>{flagTotal} responses</span> : null}
        </div>
        {flagTotal > 0 ? (
          <>
            <div className="flag-stack" aria-label="Flag to organisation yes versus no">
              <span
                aria-label={`Yes: ${flagYesCount}, ${flagYesPercentage}%`}
                className="flag-segment flag-yes"
                role="img"
                style={{ flexGrow: flagYesCount }}
                title={`Yes: ${flagYesCount} · ${flagYesPercentage}%`}
              />
              <span
                aria-label={`No: ${flagNoCount}, ${flagNoPercentage}%`}
                className="flag-segment flag-no"
                role="img"
                style={{ flexGrow: flagNoCount }}
                title={`No: ${flagNoCount} · ${flagNoPercentage}%`}
              />
            </div>
            <div className="flag-legend">
              <span>
                <i className="flag-dot flag-yes" /> Yes
              </span>
              <strong>
                {flagYesCount} · {flagYesPercentage}%
              </strong>
              <span>
                <i className="flag-dot flag-no" /> No
              </span>
              <strong>
                {flagNoCount} · {flagNoPercentage}%
              </strong>
            </div>
          </>
        ) : (
          <p className="empty-state compact">No organisation-flag responses yet.</p>
        )}
      </div>

      <label className="rate-field">
        Cost per hour
        <span className="currency-input">
          <span>£</span>
          <input
            inputMode="decimal"
            min="0"
            onChange={(event) => handleHourlyRateChange(event.target.value)}
            placeholder={String(DEFAULT_HOURLY_RATE)}
            type="text"
            value={hourlyRateInput}
          />
        </span>
      </label>
    </section>
  )
}

function loadSavedHourlyRate(storageKey: string): string {
  try {
    const saved = window.localStorage.getItem(storageKey)
    return saved ? cleanHourlyRateInput(saved) : String(DEFAULT_HOURLY_RATE)
  } catch {
    return String(DEFAULT_HOURLY_RATE)
  }
}

function saveHourlyRate(storageKey: string, value: string): void {
  try {
    if (value) {
      window.localStorage.setItem(storageKey, value)
    } else {
      window.localStorage.removeItem(storageKey)
    }
  } catch {
    // Local storage only preserves convenience state; calculation still works.
  }
}
