import type { ReactNode } from 'react'

type ErrorStateProps = {
  children?: ReactNode
}

export function ErrorState({ children }: ErrorStateProps) {
  return (
    <main className="state-shell">
      <section className="state-panel" role="alert">
        <p className="eyebrow">Aether Glimpse</p>
        <h1>Dashboard unavailable</h1>
        <p>This dashboard is not currently available. Please try again later.</p>
      </section>
      {children}
    </main>
  )
}
