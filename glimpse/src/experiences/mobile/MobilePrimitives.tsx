import type { ReactNode } from 'react'
import launchBackground from '../../assets/launch/launch-background.jpg'
import watermarkLeft from '../../assets/onboarding/watermark-left.svg'
import watermarkRight from '../../assets/onboarding/watermark-right.svg'
import { iconAetherCoach, iconUserCloud } from './mobileAssets'

type MobileFrameProps = {
  children: ReactNode
  label?: string
}

export function MobileFrame({ children, label = 'Aether Glimpse mobile experience' }: MobileFrameProps) {
  return (
    <main
      aria-label={label}
      data-testid="mobile-experience"
      className="relative min-h-[100svh] overflow-hidden bg-white text-[#294744]"
    >
      <img
        src={launchBackground}
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-0 h-full min-h-[844px] w-[1196px] max-w-none -translate-x-1/2 object-cover object-center"
      />
      <div className="relative mx-auto h-[844px] w-full max-w-[390px] overflow-hidden">
        {children}
      </div>
    </main>
  )
}

export function MobileWatermark() {
  return (
    <div className="pointer-events-none absolute left-1/2 top-[37px] h-[25px] w-[38px] -translate-x-1/2 opacity-[0.07]">
      <div className="absolute inset-[0.13%_44.81%_0_0]">
        <img
          src={watermarkLeft}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 h-full w-full max-w-none"
        />
      </div>
      <div className="absolute inset-[0_0_0.13%_44.81%]">
        <img
          src={watermarkRight}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 h-full w-full max-w-none"
        />
      </div>
    </div>
  )
}

export function MobileFullCard({ children }: { children: ReactNode }) {
  return (
    <section className="absolute left-[18px] top-[80px] h-[746px] w-[354px] rounded-[30px] border-4 border-[rgba(41,71,68,0.07)] bg-[rgba(255,255,255,0.5)]">
      {children}
    </section>
  )
}

export function MobileHalfCard({
  children,
  top,
}: {
  children: ReactNode
  top: number
}) {
  return (
    <section
      className="absolute left-[18px] h-[371px] w-[354px] rounded-[30px] border-4 border-[rgba(41,71,68,0.07)] bg-[rgba(255,255,255,0.5)]"
      style={{ top }}
    >
      {children}
    </section>
  )
}

type MobileButtonProps = {
  disabled?: boolean
  label: string
  onClick: () => void
  top?: number
}

export function MobileButton({ disabled = false, label, onClick, top = 762 }: MobileButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        'absolute left-[40px] h-[42px] w-[310px] rounded-[16px] border-[1.5px] border-[#dbec03] text-center text-[17px] font-bold leading-none',
        disabled
          ? 'cursor-not-allowed bg-transparent text-[rgba(41,71,68,0.5)]'
          : 'cursor-pointer bg-[linear-gradient(90deg,#dbec03_0%,#75b83b_100%)] text-white',
      ].join(' ')}
      style={{ top }}
    >
      {label}
    </button>
  )
}

export function MobilePrimaryIcon({ variant }: { variant: 'aether' | 'user' }) {
  return (
    <img
      src={variant === 'aether' ? iconAetherCoach : iconUserCloud}
      alt=""
      aria-hidden="true"
      className="absolute left-1/2 top-[26px] h-[40px] w-[40px] -translate-x-1/2"
    />
  )
}

export function MobileError({ children }: { children?: ReactNode }) {
  if (!children) {
    return null
  }

  return (
    <p
      role="alert"
      className="absolute left-[40px] top-[724px] m-0 w-[310px] text-center text-[12px] font-light leading-tight text-[#294744]"
    >
      {children}
    </p>
  )
}

export function MobileSelectionDot({ selected }: { selected: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={[
        'inline-block size-[14px] rounded-full border border-[#75b83b]',
        selected ? 'bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]' : 'bg-transparent',
      ].join(' ')}
    />
  )
}
