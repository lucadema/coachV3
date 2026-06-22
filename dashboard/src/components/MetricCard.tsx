type MetricCardProps = {
  label: string
  value: string
  suffix?: string
}

export function MetricCard({ label, value, suffix }: MetricCardProps) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {suffix ? <small>{suffix}</small> : null}
    </article>
  )
}
