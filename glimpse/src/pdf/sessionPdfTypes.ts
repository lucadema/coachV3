import type { PathwayCard } from '../types/session'

export type SessionPdfData = {
  problemStatement: string
  synthesis: string
  pathways: PathwayCard[]
}

export type SessionPdfSourceData = {
  problemStatement?: string
  rawPathwaysText?: string
  synthesis?: string
  pathways?: PathwayCard[]
}

export type SessionPdfSection = {
  body: string
  title: string
}
