import { useEffect, useState } from 'react'
import { LaunchScreen } from './screens/LaunchScreen'
import { OnboardingCompleteScreen } from './screens/OnboardingCompleteScreen'
import { PrivacyScreen } from './screens/PrivacyScreen'
import { WelcomeScreen } from './screens/WelcomeScreen'
import type { OnboardingStep } from './types/onboarding'

const SPLASH_DELAY_MS = 3000

function App() {
  const [step, setStep] = useState<OnboardingStep>('launch')
  const [hasAcknowledgedPrivacy, setHasAcknowledgedPrivacy] = useState(false)

  useEffect(() => {
    if (step !== 'launch' && step !== 'welcome') {
      return undefined
    }

    const nextStep: OnboardingStep = step === 'launch' ? 'welcome' : 'privacy'
    const timeoutId = window.setTimeout(() => {
      setStep(nextStep)
    }, SPLASH_DELAY_MS)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [step])

  if (step === 'launch') {
    return <LaunchScreen />
  }

  if (step === 'welcome') {
    return <WelcomeScreen />
  }

  if (step === 'privacy') {
    return (
      <PrivacyScreen
        hasAcknowledged={hasAcknowledgedPrivacy}
        onAcknowledgedChange={setHasAcknowledgedPrivacy}
        onContinue={() => {
          if (!hasAcknowledgedPrivacy) {
            return
          }

          setStep('complete')
        }}
      />
    )
  }

  return <OnboardingCompleteScreen />
}

export default App
