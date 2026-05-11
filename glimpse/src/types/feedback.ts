export const valuableMomentOptions = [
  'Being asked a question I hadn’t thought to ask myself',
  'The moment Aether reflected my challenge back to me accurately',
  'Seeing my problem restated clearly in one place',
  'Receiving structured pathways rather than a generic answer',
  'The feeling that I was being guided rather than just given information',
  'Having a confidential space to think without judgement',
] as const

export type ValuableMomentOption = (typeof valuableMomentOptions)[number]

export type FeedbackState = {
  helpedThinkDifferently: boolean | null
  organisationalBenefit: boolean | null
  valuableMoments: string[]
}

export function createDefaultFeedbackState(): FeedbackState {
  return {
    helpedThinkDifferently: null,
    organisationalBenefit: null,
    valuableMoments: [],
  }
}
