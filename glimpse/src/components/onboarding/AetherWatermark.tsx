import watermarkLeft from '../../assets/onboarding/watermark-left.svg'
import watermarkRight from '../../assets/onboarding/watermark-right.svg'

type AetherWatermarkProps = {
  className?: string
}

export function AetherWatermark({ className }: AetherWatermarkProps) {
  const watermarkClassName = ['relative h-[40.653px] w-[60.501px] opacity-[0.07]', className]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={watermarkClassName}>
      <div className="absolute inset-[0.13%_44.81%_0_0]">
        <img
          src={watermarkLeft}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 size-full max-w-none"
        />
      </div>
      <div className="absolute inset-[0_0_0.13%_44.81%]">
        <img
          src={watermarkRight}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 size-full max-w-none"
        />
      </div>
    </div>
  )
}
