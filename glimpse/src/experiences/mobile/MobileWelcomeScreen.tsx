import { MobileFrame, MobileWatermark } from './MobilePrimitives'

export function MobileWelcomeScreen() {
  return (
    <MobileFrame label="Aether Glimpse mobile welcome">
      <MobileWatermark />
      <h1 className="absolute left-[-12px] top-[314px] m-0 w-[414px] text-center text-[70px] font-thin leading-[70px] tracking-[-2.8px] text-[#294744]">
        Welcome
        <br />
        to Aether
        <br />
        Glimpse
      </h1>
      <div className="absolute left-[23px] top-[624px] w-[344px] text-center text-[18px] font-light leading-none tracking-[-0.72px]">
        <p className="m-0">Together we’ll explore a challenge</p>
        <p className="m-0">you’re facing at work.</p>
        <p className="m-0 mt-[29px]">Before we get stuck in, there’s a few</p>
        <p className="m-0">things we need to agree on.</p>
      </div>
    </MobileFrame>
  )
}
