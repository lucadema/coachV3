import type { ChartBucket } from '../data/dashboardTransforms'

const SIGNAL_CLASS_BY_VALUE: Record<string, string> = {
  no_visible_risk: 'signal-green',
  frustration_signal: 'signal-amber',
  voice_suppression_signal: 'signal-orange',
  disengagement_risk: 'signal-red',
}

type StackedSignalBarProps = {
  segments: ChartBucket[]
}

export function StackedSignalBar({ segments }: StackedSignalBarProps) {
  return (
    <div className="signal-stack-wrap">
      <div className="signal-stack" aria-label="Engagement health signal distribution">
        {segments.map((segment) => (
          <span
            aria-label={`${segment.label}: ${segment.count}, ${segment.percentage}%`}
            className={`signal-segment ${SIGNAL_CLASS_BY_VALUE[segment.value] ?? ''}`}
            key={segment.value}
            role="img"
            style={{ flexGrow: segment.count, flexBasis: segment.count > 0 ? '24px' : '0' }}
            title={`${segment.label}: ${segment.count} · ${segment.percentage}%`}
          />
        ))}
      </div>
      <div className="signal-legend">
        {segments.map((segment) => (
          <div className="legend-item" key={segment.value}>
            <span className={`legend-dot ${SIGNAL_CLASS_BY_VALUE[segment.value] ?? ''}`} />
            <span>{segment.label}</span>
            <strong>
              {segment.count} · {segment.percentage}%
            </strong>
          </div>
        ))}
      </div>
    </div>
  )
}
