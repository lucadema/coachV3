import { DesktopExperience } from './experiences/DesktopExperience'
import { MobileExperience } from './experiences/MobileExperience'
import { useExperienceMode } from './flow/useExperienceMode'
import { useGlimpseSession } from './flow/useGlimpseSession'

function App() {
  const flow = useGlimpseSession()
  const experienceMode = useExperienceMode()

  if (experienceMode === 'mobile') {
    return <MobileExperience flow={flow} />
  }

  return <DesktopExperience flow={flow} />
}

export default App
