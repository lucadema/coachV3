import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileFullCard,
  MobileWatermark,
} from './MobilePrimitives'
import { iconAetherCoach, iconUserCloud } from './mobileAssets'

type MobileInformationScreenProps = {
  error?: string | null
  isLoading?: boolean
  onStartSession: () => void
}

export function MobileInformationScreen({
  error = null,
  isLoading = false,
  onStartSession,
}: MobileInformationScreenProps) {
  return (
    <MobileFrame label="Aether Glimpse mobile information">
      <MobileWatermark />
      <MobileFullCard>
        <div className="absolute left-[22px] top-[100px] w-[310px] text-center text-[18px] font-light leading-none tracking-[-0.72px]">
          <p className="m-0">This is a space to explore</p>
          <p className="m-0">one professional challenge</p>
          <p className="m-0">with clarity and depth.</p>
          <p className="m-0 mt-[29px]">Aether will ask you questions</p>
          <p className="m-0">that help you understand</p>
          <p className="m-0">your problem more fully</p>
          <p className="m-0">before presenting a set of</p>
          <p className="m-0">resolution pathways you</p>
          <p className="m-0">can take away and act on.</p>
        </div>
        <img src={iconUserCloud} alt="" aria-hidden="true" className="absolute left-[119px] top-[407px] h-[40px] w-[40px]" />
        <img src={iconAetherCoach} alt="" aria-hidden="true" className="absolute left-[193px] top-[407px] h-[40px] w-[40px]" />
        <div className="absolute left-[22px] top-[554px] w-[310px] text-center text-[18px] font-light leading-none tracking-[-0.72px]">
          <p className="m-0">Throughout the session, the</p>
          <p className="m-0">thinking cloud icon represents you.</p>
          <p className="m-0">The green ‘a’ icon represents Aether.</p>
        </div>
      </MobileFullCard>
      <MobileError>{error}</MobileError>
      <MobileButton
        disabled={isLoading}
        label={isLoading ? 'Starting...' : 'Start Session'}
        onClick={onStartSession}
      />
    </MobileFrame>
  )
}
