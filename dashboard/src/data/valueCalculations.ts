export const DEFAULT_HOURLY_RATE = 30
export const HOURS_PER_MINUTE = 1 / 60
export const MONTHS_PER_YEAR = 12

export type ValueMetrics = {
  monthlyHours: number
  monthlyValue: number
  annualValue: number
}

export function cleanHourlyRateInput(value: string): string {
  if (value.includes('-')) {
    return '0'
  }

  const stripped = value.replace(/[^\d.]/g, '')
  const [whole, ...fractionParts] = stripped.split('.')
  const fraction = fractionParts.join('')

  if (fractionParts.length === 0) {
    return whole
  }

  return `${whole}.${fraction}`
}

export function parseHourlyRate(value: string): number | null {
  const cleaned = cleanHourlyRateInput(value)
  if (!cleaned || cleaned === '.') {
    return null
  }

  const parsed = Number(cleaned)
  if (!Number.isFinite(parsed)) {
    return null
  }

  return Math.max(0, parsed)
}

export function calculateValueMetrics(
  monthlyMinutes: number,
  hourlyRate: number | null,
): ValueMetrics {
  const safeMinutes = Number.isFinite(monthlyMinutes) ? Math.max(0, monthlyMinutes) : 0
  const safeHourlyRate = hourlyRate === null ? 0 : Math.max(0, hourlyRate)
  const monthlyHours = safeMinutes * HOURS_PER_MINUTE
  const monthlyValue = monthlyHours * safeHourlyRate

  return {
    monthlyHours,
    monthlyValue,
    annualValue: monthlyValue * MONTHS_PER_YEAR,
  }
}

export function formatHours(value: number): string {
  return new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: value >= 10 ? 0 : 1,
  }).format(value)
}

export function formatCurrencyGBP(value: number): string {
  return new Intl.NumberFormat('en-GB', {
    currency: 'GBP',
    maximumFractionDigits: 0,
    style: 'currency',
  }).format(value)
}

export function hourlyRateStorageKey(tokenKey: string): string {
  return `glimpse_dashboard_hourly_rate_${tokenKey}`
}
