import type { jsPDF } from 'jspdf'
import type { PathwayCard } from '../types/session'
import type { SessionPdfData, SessionPdfSection, SessionPdfSourceData } from './sessionPdfTypes'

const pageMargin = 18
const pageWidth = 210
const pageHeight = 297
const contentWidth = pageWidth - pageMargin * 2
const footerY = pageHeight - 10
const sectionGap = 8

type PdfCursor = {
  y: number
}

function normaliseText(value: string | null | undefined): string {
  return String(value ?? '').trim()
}

function normalisePathways(pathways: PathwayCard[] | undefined): PathwayCard[] {
  return (pathways ?? []).flatMap((pathway) => {
    const title = normaliseText(pathway.title)
    const body = normaliseText(pathway.body)

    if (!title && !body) {
      return []
    }

    return [
      {
        title: title || 'Pathway',
        body,
      },
    ]
  })
}

export function buildSessionPdfData(source: SessionPdfSourceData): SessionPdfData {
  const pathways = normalisePathways(source.pathways)
  const rawPathwaysText = normaliseText(source.rawPathwaysText)

  return {
    problemStatement: normaliseText(source.problemStatement),
    synthesis: normaliseText(source.synthesis),
    pathways:
      pathways.length > 0 || !rawPathwaysText
        ? pathways
        : [
            {
              title: 'Pathways',
              body: rawPathwaysText,
            },
          ],
  }
}

export function buildSessionPdfSections(data: SessionPdfData): SessionPdfSection[] {
  const sections: SessionPdfSection[] = []

  if (data.problemStatement) {
    sections.push({
      title: 'Problem statement',
      body: data.problemStatement,
    })
  }

  if (data.synthesis) {
    sections.push({
      title: 'Synthesised understanding',
      body: data.synthesis,
    })
  }

  if (data.pathways.length > 0) {
    sections.push({
      title: 'Pathways',
      body: data.pathways
        .map((pathway) => `${pathway.title}\n${pathway.body || 'No pathway detail provided.'}`)
        .join('\n\n'),
    })
  }

  if (sections.length === 0) {
    sections.push({
      title: 'Session notes',
      body: 'No session details were available for this download.',
    })
  }

  return sections
}

function ensureSpace(doc: jsPDF, cursor: PdfCursor, requiredHeight: number) {
  if (cursor.y + requiredHeight <= footerY - 8) {
    return
  }

  doc.addPage()
  cursor.y = pageMargin
}

function writeWrappedText({
  cursor,
  doc,
  fontSize,
  lineHeight,
  maxWidth = contentWidth,
  text,
  x = pageMargin,
}: {
  cursor: PdfCursor
  doc: jsPDF
  fontSize: number
  lineHeight: number
  maxWidth?: number
  text: string
  x?: number
}) {
  doc.setFontSize(fontSize)

  const paragraphs = text.split(/\n+/)
  paragraphs.forEach((paragraph, paragraphIndex) => {
    const lines = doc.splitTextToSize(paragraph || ' ', maxWidth) as string[]

    lines.forEach((line) => {
      ensureSpace(doc, cursor, lineHeight)
      doc.text(line, x, cursor.y)
      cursor.y += lineHeight
    })

    if (paragraphIndex < paragraphs.length - 1) {
      cursor.y += lineHeight / 2
    }
  })
}

function writeFooter(doc: jsPDF) {
  const totalPages = doc.getNumberOfPages()

  for (let pageNumber = 1; pageNumber <= totalPages; pageNumber += 1) {
    doc.setPage(pageNumber)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(100, 120, 116)
    doc.text('Aether Glimpse', pageMargin, footerY)
    doc.text(`${pageNumber}/${totalPages}`, pageWidth - pageMargin, footerY, {
      align: 'right',
    })
  }
}

export function renderSessionPdfLayout(doc: jsPDF, data: SessionPdfData) {
  const cursor: PdfCursor = { y: pageMargin }

  doc.setProperties({
    title: 'Aether Glimpse session summary',
    subject: 'Aether Glimpse problem statement, synthesis, and pathways',
  })

  doc.setFillColor(219, 236, 3)
  doc.rect(0, 0, pageWidth, 18, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(16)
  doc.setTextColor(41, 71, 68)
  doc.text('Aether Glimpse', pageMargin, 12)

  cursor.y = 30

  buildSessionPdfSections(data).forEach((section) => {
    ensureSpace(doc, cursor, 16)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(13)
    doc.setTextColor(41, 71, 68)
    doc.text(section.title, pageMargin, cursor.y)
    cursor.y += 8

    doc.setFont('helvetica', 'normal')
    doc.setTextColor(41, 71, 68)
    writeWrappedText({
      cursor,
      doc,
      fontSize: 11,
      lineHeight: 6,
      text: section.body,
    })
    cursor.y += sectionGap
  })

  writeFooter(doc)
}
