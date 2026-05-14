import { MobileButton, MobileFrame, MobileWatermark } from './MobilePrimitives'

export function MobileClosedScreen() {
  return (
    <MobileFrame label="Aether Glimpse mobile closed">
      <MobileWatermark />
      <h1 className="absolute left-[37px] top-[222px] m-0 w-[310px] text-center text-[70px] font-thin leading-[70px] tracking-[-2.8px]">
        We hope
        <br />
        you’ve enjoyed
        <br />
        this
        <br />
        glimpse
        <br />
        of Aether
      </h1>
      <MobileButton label="Start New Session" onClick={() => window.location.reload()} top={766} />
    </MobileFrame>
  )
}
