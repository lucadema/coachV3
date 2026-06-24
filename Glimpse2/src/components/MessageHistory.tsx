import type { ConversationExchange } from '../types/session'
import { MarkdownText } from './MarkdownText'

type MessageHistoryProps = {
  exchanges: ConversationExchange[]
}

export function MessageHistory({ exchanges }: MessageHistoryProps) {
  if (exchanges.length === 0) {
    return (
      <aside className="history-panel">
        <div className="panel-kicker">Previous exchanges</div>
        <p className="muted-copy">Your earlier responses will appear here as the session unfolds.</p>
      </aside>
    )
  }

  return (
    <aside className="history-panel">
      <div className="panel-kicker">Previous exchanges</div>
      <div className="exchange-list">
        {exchanges.map((exchange) => (
          <article className="exchange" key={exchange.id}>
            <div className="exchange-user">{exchange.userMessage}</div>
            {exchange.coachMessage ? (
              <div className="exchange-coach">
                <MarkdownText text={exchange.coachMessage} />
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </aside>
  )
}
