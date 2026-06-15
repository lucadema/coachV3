export type LaunchContext = {
  accessToken?: string
  sessionLabel?: string
}

const SESSION_LABEL_PATTERN = /^[a-z0-9_.-]{1,64}$/
const ACCESS_TOKEN_PATTERN = /^[A-Za-z0-9_-]{20,256}$/

export function sanitizeSessionLabel(value: string | null | undefined): string | undefined {
  const normalized = value?.trim().toLowerCase()

  if (!normalized || !SESSION_LABEL_PATTERN.test(normalized)) {
    return undefined
  }

  return normalized
}

export function sanitizeAccessToken(value: string | null | undefined): string | undefined {
  const normalized = value?.trim()

  if (!normalized || !ACCESS_TOKEN_PATTERN.test(normalized)) {
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
    const accessToken = sanitizeAccessToken(params.get('t') ?? params.get('token'))

    return {
      ...(accessToken ? { accessToken } : {}),
      ...(sessionLabel ? { sessionLabel } : {}),
    }
  } catch {
    return {}
  }
}
