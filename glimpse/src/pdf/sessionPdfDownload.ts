import { downloadAetherGlimpsePdf, type AetherGlimpsePdfData } from './aetherGlimpsePdf'
import type { SessionPdfData } from './sessionPdfTypes'

const pdfTitle = 'Aether Glimpse'
const pdfIntro =
  'Below is a synthesis of the session you have been working through with the Aether thinking coach. We hope the experience has been enjoyable and helped you move closer to resolving your work challenge.'

function normaliseText(value: string | null | undefined): string {
  return String(value ?? '').trim()
}

function splitPathwayBody(
  body: string,
): Pick<AetherGlimpsePdfData['pathways'][number], 'orientation' | 'conditions'> {
  const source = normaliseText(body)
  const orientationMatch = source.match(/(?:^|\n)\s*Orientation:\s*([\s\S]*?)(?=(?:\n\s*Conditions:\s*)|$)/i)
  const conditionsMatch = source.match(/(?:^|\n)\s*Conditions:\s*([\s\S]*)$/i)

  if (!orientationMatch && !conditionsMatch) {
    return {
      orientation: source,
      conditions: '',
    }
  }

  return {
    orientation: normaliseText(orientationMatch?.[1]),
    conditions: normaliseText(conditionsMatch?.[1]),
  }
}

export function buildAetherGlimpsePdfData(data: SessionPdfData): AetherGlimpsePdfData {
  return {
    title: pdfTitle,
    intro: pdfIntro,
    problemDefinition: normaliseText(data.synthesis),
    pathways: data.pathways.map((pathway) => ({
      title: normaliseText(pathway.title),
      ...splitPathwayBody(pathway.body),
    })),
  }
}

export async function downloadSessionPdf(
  data: SessionPdfData,
  fileName = 'aether-glimpse-session.pdf',
): Promise<void> {
  await downloadAetherGlimpsePdf(buildAetherGlimpsePdfData(data), {
    filename: fileName,
  })
}
