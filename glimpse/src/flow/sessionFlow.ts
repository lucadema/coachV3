import type { BackendSessionView, FrontendScreen, PathwayCard } from '../types/session'

const BACKEND_STAGE_TO_SCREEN: Record<string, FrontendScreen> = {
  classification: 'coaching',
  coaching: 'coaching',
  synthesis: 'synthesis_review',
  pathways: 'pathways',
  closure: 'feedback',
}

export function mapBackendToScreen(session: BackendSessionView | null | undefined): FrontendScreen {
  return BACKEND_STAGE_TO_SCREEN[String(session?.stage ?? '')] ?? 'coaching'
}

export function isRefinedSynthesisWaitingForPathways(
  session: BackendSessionView | null | undefined,
): boolean {
  return session?.stage === 'pathways' && session.state === 'preparing'
}

export function parsePathwayCards(text: string | null | undefined): PathwayCard[] {
  const source = String(text ?? '').trim()
  if (!source) {
    return []
  }

  const headingMatches = Array.from(source.matchAll(/^##\s+(.+?)\s*$/gm))
  if (headingMatches.length === 0) {
    return []
  }

  return headingMatches.flatMap((match, index) => {
    const title = match[1]?.trim() ?? ''
    const bodyStart = match.index + match[0].length
    const bodyEnd =
      index + 1 < headingMatches.length ? headingMatches[index + 1].index : source.length
    const body = source.slice(bodyStart, bodyEnd).trim()

    if (!title || !body) {
      return []
    }

    return [{ title, body }]
  })
}
