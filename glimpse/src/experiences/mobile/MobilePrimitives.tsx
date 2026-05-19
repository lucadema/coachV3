import { useEffect, useState, type ReactNode } from 'react'
import launchBackground from '../../assets/launch/launch-background.jpg'
import watermarkLeft from '../../assets/onboarding/watermark-left.svg'
import watermarkRight from '../../assets/onboarding/watermark-right.svg'
import { iconAetherCoach, iconUserCloud } from './mobileAssets'

const MOBILE_DESIGN_WIDTH = 390
const MOBILE_DESIGN_HEIGHT = 844

type MobileFrameProps = {
  children: ReactNode
  label?: string
}

function getMobileCanvasScale() {
  if (typeof window === 'undefined') {
    return 1
  }

  const viewportWidth = window.visualViewport?.width ?? window.innerWidth

  return Math.min(viewportWidth / MOBILE_DESIGN_WIDTH, 1)
}

export function MobileFrame({ children, label = 'Aether Glimpse mobile experience' }: MobileFrameProps) {
  const [scale, setScale] = useState(getMobileCanvasScale)

  useEffect(() => {
    const handleResize = () => {
      setScale(getMobileCanvasScale())
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    window.visualViewport?.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.visualViewport?.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <main
      aria-label={label}
      data-testid="mobile-experience"
      className="relative min-h-[100svh] overflow-x-hidden overflow-y-auto bg-white text-[#294744]"
    >
      <img
        src={launchBackground}
        alt=""
        aria-hidden="true"
        className="pointer-events-none fixed left-1/2 top-0 h-full min-h-[844px] w-[1196px] max-w-none -translate-x-1/2 object-cover object-center"
      />
      <div
        className="relative mx-auto overflow-visible"
        style={{
          height: MOBILE_DESIGN_HEIGHT * scale,
          width: MOBILE_DESIGN_WIDTH * scale,
        }}
      >
        <div
          className="relative h-[844px] w-[390px] origin-top-left"
          style={{
            transform: `scale(${scale})`,
          }}
        >
          {children}
        </div>
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
    <section className="absolute left-1/2 top-[80px] h-[746px] w-[calc(100%_-_36px)] max-w-[354px] -translate-x-1/2 rounded-[30px] border-4 border-[rgba(41,71,68,0.07)] bg-[rgba(255,255,255,0.5)]">
      {children}
    </section>
  )
}

export function MobileHalfCard({
  children,
  opaque = false,
  top,
}: {
  children: ReactNode
  opaque?: boolean
  top: number
}) {
  return (
    <section
      className={[
        'absolute left-1/2 h-[371px] w-[calc(100%_-_36px)] max-w-[354px] -translate-x-1/2 rounded-[30px] border-4 border-[rgba(41,71,68,0.07)]',
        opaque ? 'bg-white' : 'bg-[rgba(255,255,255,0.5)]',
      ].join(' ')}
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
        'absolute left-1/2 h-[42px] w-[calc(100%_-_80px)] max-w-[310px] -translate-x-1/2 rounded-[16px] border-[1.5px] border-[#dbec03] bg-transparent text-center text-[17px] font-bold leading-none text-[rgba(41,71,68,0.5)] transition-colors duration-100 active:bg-[linear-gradient(90deg,#dbec03_0%,#75b83b_100%)] active:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#75b83b]',
        disabled ? 'cursor-not-allowed' : 'cursor-pointer',
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
        'inline-block size-[18px] shrink-0 rounded-full border-[1.5px] border-[#75b83b] bg-white shadow-[0_0_0_2px_rgba(255,255,255,0.65)]',
        selected ? 'bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]' : 'bg-white',
      ].join(' ')}
    />
  )
}
