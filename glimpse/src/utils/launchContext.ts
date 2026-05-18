export type LaunchContext = {
  sessionLabel?: string
}

const SESSION_LABEL_PATTERN = /^[a-z0-9_.-]{1,64}$/

export function sanitizeSessionLabel(value: string | null | undefined): string | undefined {
  const normalized = value?.trim().toLowerCase()

  if (!normalized || !SESSION_LABEL_PATTERN.test(normalized)) {
    return undefined
  }

  return normalized
}

export function getLaunchContext(): LaunchContext {
  try {
    if (typeof window === 'undefined') {
      return {}
    }

    const params = new URLSearchParams(window.location.search)
    const sessionLabel = sanitizeSessionLabel(params.get('session_label'))

    return sessionLabel ? { sessionLabel } : {}
  } catch {
    return {}
  }
}
