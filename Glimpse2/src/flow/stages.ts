import type { BackendSessionView, ExperienceStep, FrontendScreen, PathwayCard } from '../types/session'
import type { StageDefinition } from '../types/experience'

const BACKEND_STAGE_TO_SCREEN: Record<string, FrontendScreen> = {
  classification: 'coaching',
  coaching: 'coaching',
  synthesis: 'synthesis_review',
  pathways: 'pathways',
  closure: 'feedback',
}

export const STAGE_DEFINITIONS: Record<ExperienceStep, StageDefinition> = {
  launch: {
    step: 'launch',
    label: 'Arrival',
    shortLabel: 'Arrival',
    progress: 2,
    phase: 'arrival',
  },
  privacy: {
    step: 'privacy',
    label: 'Privacy',
    shortLabel: 'Privacy',
    progress: 8,
    phase: 'consent',
  },
  intro: {
    step: 'intro',
    label: 'Prepare',
    shortLabel: 'Prepare',
    progress: 14,
    phase: 'setup',
  },
  problem_input: {
    step: 'problem_input',
    label: 'Define the challenge',
    shortLabel: 'Define',
    progress: 24,
    phase: 'exploration',
  },
  coaching: {
    step: 'coaching',
    label: 'Explore',
    shortLabel: 'Explore',
    progress: 45,
    phase: 'exploration',
  },
  synthesis_review: {
    step: 'synthesis_review',
    label: 'Review synthesis',
    shortLabel: 'Synthesis',
    progress: 66,
    phase: 'review',
  },
  pathways: {
    step: 'pathways',
    label: 'Consider pathways',
    shortLabel: 'Pathways',
    progress: 82,
    phase: 'review',
  },
  feedback_query: {
    step: 'feedback_query',
    label: 'Feedback',
    shortLabel: 'Feedback',
    progress: 92,
    phase: 'feedback',
  },
  feedback: {
    step: 'feedback',
    label: 'Feedback',
    shortLabel: 'Feedback',
    progress: 96,
    phase: 'feedback',
  },
  closed: {
    step: 'closed',
    label: 'Complete',
    shortLabel: 'Complete',
    progress: 100,
    phase: 'complete',
  },
  backend_response: {
    step: 'backend_response',
    label: 'Response',
    shortLabel: 'Response',
    progress: 50,
    phase: 'exploration',
  },
}

export const PROGRESS_MILESTONES: ExperienceStep[] = [
  'problem_input',
  'coaching',
  'synthesis_review',
  'pathways',
  'feedback',
  'closed',
]

export function mapBackendToScreen(session: BackendSessionView | null | undefined): FrontendScreen {
  if (session?.cancelled || session?.completed) {
    return session?.stage === 'closure' ? 'feedback' : 'closed'
  }

  return BACKEND_STAGE_TO_SCREEN[String(session?.stage ?? '')] ?? 'coaching'
}

export function stepFromBackendSession(
  session: BackendSessionView | null | undefined,
): ExperienceStep {
  const screen = mapBackendToScreen(session)
  return screen === 'feedback' ? 'feedback_query' : screen
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
    const bodyStart = (match.index ?? 0) + match[0].length
    const bodyEnd =
      index + 1 < headingMatches.length
        ? (headingMatches[index + 1].index ?? source.length)
        : source.length
    const body = source.slice(bodyStart, bodyEnd).trim()

    if (!title || !body) {
      return []
    }

    return [{ title, body }]
  })
}
