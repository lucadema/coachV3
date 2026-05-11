import { jsPDF } from 'jspdf'
import { renderSessionPdfLayout } from './sessionPdfLayout'
import type { SessionPdfData } from './sessionPdfTypes'

export function generateSessionPdf(data: SessionPdfData): jsPDF {
  const doc = new jsPDF({
    format: 'a4',
    orientation: 'portrait',
    unit: 'mm',
  })

  renderSessionPdfLayout(doc, data)

  return doc
}
