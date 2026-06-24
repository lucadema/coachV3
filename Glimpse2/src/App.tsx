import { AppShell } from './components/AppShell'
import { BackendResponseScreen } from './screens/BackendResponseScreen'
import { ClosedScreen } from './screens/ClosedScreen'
import { CoachingScreen } from './screens/CoachingScreen'
import { FeedbackQueryScreen } from './screens/FeedbackQueryScreen'
import { FeedbackScreen } from './screens/FeedbackScreen'
import { IntroScreen } from './screens/IntroScreen'
import { LaunchScreen } from './screens/LaunchScreen'
import { PathwaysScreen } from './screens/PathwaysScreen'
import { PrivacyScreen } from './screens/PrivacyScreen'
import { ProblemInputScreen } from './screens/ProblemInputScreen'
import { SynthesisReviewScreen } from './screens/SynthesisReviewScreen'
import { useGlimpseExperience } from './session/useGlimpseExperience'

function App() {
  const flow = useGlimpseExperience()

  return <AppShell flow={flow}>{renderScreen(flow)}</AppShell>
}

function renderScreen(flow: ReturnType<typeof useGlimpseExperience>) {
  switch (flow.current.step) {
    case 'launch':
      return <LaunchScreen flow={flow} />
    case 'privacy':
      return <PrivacyScreen flow={flow} />
    case 'intro':
      return <IntroScreen flow={flow} />
    case 'problem_input':
      return <ProblemInputScreen flow={flow} />
    case 'coaching':
      return <CoachingScreen flow={flow} />
    case 'synthesis_review':
      return <SynthesisReviewScreen flow={flow} />
    case 'pathways':
      return <PathwaysScreen flow={flow} />
    case 'feedback_query':
      return <FeedbackQueryScreen flow={flow} />
    case 'feedback':
      return <FeedbackScreen flow={flow} />
    case 'closed':
      return <ClosedScreen flow={flow} />
    case 'backend_response':
      return <BackendResponseScreen flow={flow} />
    default:
      return <LaunchScreen flow={flow} />
  }
}

export default App
