import type { ReactNode } from 'react'

type UnavailableStateProps = {
  children?: ReactNode
}

export function UnavailableState({ children }: UnavailableStateProps) {
  return (
    <main className="state-shell">
      <section className="state-panel">
        <p className="eyebrow">Aether Glimpse</p>
        <h1>Dashboard unavailable</h1>
        <p>This dashboard is not currently available for this pilot.</p>
      </section>
      {children}
    </main>
  )
}
