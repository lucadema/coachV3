import type { ReactNode } from 'react'

type LoadingStateProps = {
  children?: ReactNode
}

export function LoadingState({ children }: LoadingStateProps) {
  return (
    <main className="state-shell">
      <section className="state-panel" aria-live="polite">
        <p className="eyebrow">Aether Glimpse</p>
        <h1>Loading dashboard</h1>
        <p>Preparing the pilot summary.</p>
      </section>
      {children}
    </main>
  )
}
