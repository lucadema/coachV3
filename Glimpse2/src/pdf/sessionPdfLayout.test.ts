import { describe, expect, it } from 'vitest'
import { generateSessionPdf } from './sessionPdfGenerator'
import { buildSessionPdfData, buildSessionPdfSections } from './sessionPdfLayout'

describe('buildSessionPdfData', () => {
  it('builds PDF data from retained session content', () => {
    expect(
      buildSessionPdfData({
        pathways: [{ title: 'Build evidence', body: 'Create the proof base.' }],
        problemStatement: 'Original problem',
        synthesis: 'Synthesised challenge',
      }),
    ).toEqual({
      pathways: [{ title: 'Build evidence', body: 'Create the proof base.' }],
      problemStatement: 'Original problem',
      synthesis: 'Synthesised challenge',
    })
  })

  it('uses raw pathway text as a fallback when cards are unavailable', () => {
    expect(
      buildSessionPdfData({
        rawPathwaysText: 'Unstructured pathway response.',
      }).pathways,
    ).toEqual([{ title: 'Pathways', body: 'Unstructured pathway response.' }])
  })

  it('handles missing optional fields without crashing', () => {
    const data = buildSessionPdfData({})

    expect(data).toEqual({
      pathways: [],
      problemStatement: '',
      synthesis: '',
    })
    expect(buildSessionPdfSections(data)).toEqual([
      {
        title: 'Session notes',
        body: 'No session details were available for this download.',
      },
    ])
    expect(() => generateSessionPdf(data)).not.toThrow()
  })
})
