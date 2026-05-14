import { MobileFrame } from './MobilePrimitives'
import { aetherWordmark } from './mobileAssets'

export function MobileLaunchScreen() {
  return (
    <MobileFrame label="Aether Glimpse mobile launch">
      <img
        src={aetherWordmark}
        alt="Aether"
        className="absolute left-[28px] top-[362px] h-[119px] w-[333px]"
      />
    </MobileFrame>
  )
}
