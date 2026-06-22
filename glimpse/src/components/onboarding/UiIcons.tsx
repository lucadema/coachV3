type IconProps = {
  className?: string
}

export function DownloadIcon({ className = 'size-[18px]' }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      <path
        d="M12 3.75v10.5m0 0 4.25-4.25M12 14.25 7.75 10M5.25 17.25v3h13.5v-3"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  )
}

export function ChevronIcon({ className = 'size-[14px]', direction = 'down' }: IconProps & { direction?: 'down' | 'up' }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className}>
      <path
        d={direction === 'up' ? 'M4 10l4-4 4 4' : 'M4 6l4 4 4-4'}
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  )
}

export function ExpandIcon({ className = 'size-[14px]' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className}>
      <path
        d="M8 3.5v9M3.5 8h9"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  )
}

export function CloseIcon({ className = 'size-[13px]' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className}>
      <path
        d="M4.25 4.25l7.5 7.5m0-7.5-7.5 7.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  )
}

export function HeartIcon({
  className = 'size-[14px]',
  filled = false,
}: IconProps & { filled?: boolean }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className}>
      <path
        d="M8 13.25s-5.25-3.08-5.25-7.02c0-1.68 1.13-2.98 2.72-2.98A2.9 2.9 0 0 1 8 4.72a2.9 2.9 0 0 1 2.53-1.47c1.59 0 2.72 1.3 2.72 2.98C13.25 10.17 8 13.25 8 13.25Z"
        fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.6"
      />
    </svg>
  )
}
