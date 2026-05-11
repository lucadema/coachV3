import { generateSessionPdf } from './sessionPdfGenerator'
import type { SessionPdfData } from './sessionPdfTypes'

export function downloadSessionPdf(data: SessionPdfData, fileName = 'aether-glimpse-session.pdf') {
  const doc = generateSessionPdf(data)
  doc.save(fileName)
}
