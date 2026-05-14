import { useEffect, useState } from 'react'

export type ExperienceMode = 'desktop' | 'mobile'

const MOBILE_MEDIA_QUERY = '(max-width: 767px)'

type LegacyMediaQueryList = MediaQueryList & {
  addListener?: (listener: (event: MediaQueryListEvent) => void) => void
  removeListener?: (listener: (event: MediaQueryListEvent) => void) => void
}

function getQueryExperienceMode(): ExperienceMode | null {
  if (typeof window === 'undefined') {
    return null
  }

  const requestedMode = new URLSearchParams(window.location.search).get('experience')

  if (requestedMode === 'mobile' || requestedMode === 'desktop') {
    return requestedMode
  }

  return null
}

function getViewportExperienceMode(): ExperienceMode {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'desktop'
  }

  return window.matchMedia(MOBILE_MEDIA_QUERY).matches ? 'mobile' : 'desktop'
}

function getExperienceMode(): ExperienceMode {
  return getQueryExperienceMode() ?? getViewportExperienceMode()
}

export function useExperienceMode(): ExperienceMode {
  const [mode, setMode] = useState<ExperienceMode>(() => getExperienceMode())

  useEffect(() => {
    if (getQueryExperienceMode()) {
      return undefined
    }

    if (typeof window.matchMedia !== 'function') {
      return undefined
    }

    const mediaQueryList: LegacyMediaQueryList = window.matchMedia(MOBILE_MEDIA_QUERY)
    const handleChange = (event: MediaQueryListEvent) => {
      setMode(event.matches ? 'mobile' : 'desktop')
    }

    if (typeof mediaQueryList.addEventListener === 'function') {
      mediaQueryList.addEventListener('change', handleChange)

      return () => {
        mediaQueryList.removeEventListener('change', handleChange)
      }
    }

    mediaQueryList.addListener?.(handleChange)

    return () => {
      mediaQueryList.removeListener?.(handleChange)
    }
  }, [])

  return mode
}
