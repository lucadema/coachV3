import { useEffect, useState } from 'react'
import { InformationScreen } from './screens/InformationScreen'
import { LaunchScreen } from './screens/LaunchScreen'
import { OnboardingCompleteScreen } from './screens/OnboardingCompleteScreen'
import { PrivacyScreen } from './screens/PrivacyScreen'
import { ProblemInputScreen } from './screens/ProblemInputScreen'
import { WelcomeScreen } from './screens/WelcomeScreen'
import type { OnboardingStep } from './types/onboarding'

const SCREEN_DELAYS: Partial<Record<OnboardingStep, number>> = {
  launch: 3000,
  welcome: 4000,
}

function App() {
  const [step, setStep] = useState<OnboardingStep>('launch')
  const [hasAcknowledgedPrivacy, setHasAcknowledgedPrivacy] = useState(false)

  useEffect(() => {
    const delay = SCREEN_DELAYS[step]

    if (delay === undefined) {
      return undefined
    }

    const nextStep: OnboardingStep = step === 'launch' ? 'welcome' : 'privacy'
    const timeoutId = window.setTimeout(() => {
      setStep(nextStep)
    }, delay)

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

          setStep('information')
        }}
      />
    )
  }

  if (step === 'information') {
    return <InformationScreen onStartSession={() => setStep('problem_input')} />
  }

  if (step === 'problem_input') {
    return <ProblemInputScreen onContinue={() => setStep('complete')} />
  }

  return <OnboardingCompleteScreen />
}

export default App
