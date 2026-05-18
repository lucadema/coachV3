import { useEffect, useState, type ReactNode } from 'react'
import launchBackground from '../../assets/launch/launch-background.jpg'

const DESIGN_WIDTH = 1451
const DESIGN_HEIGHT = 1024

type OnboardingFrameProps = {
  background?: 'launch' | 'plain'
  children: ReactNode
}

function getCanvasScale() {
  if (typeof window === 'undefined') {
    return 1
  }

  const widthScale = (window.innerWidth - 32) / DESIGN_WIDTH
  const heightScale = (window.innerHeight - 32) / DESIGN_HEIGHT

  return Math.min(widthScale, heightScale, 1)
}

export function OnboardingFrame({ background = 'launch', children }: OnboardingFrameProps) {
  const [scale, setScale] = useState(getCanvasScale)

  useEffect(() => {
    const handleResize = () => {
      setScale(getCanvasScale())
    }

    handleResize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <main className="relative flex min-h-[100svh] w-full items-center justify-center overflow-x-hidden overflow-y-auto bg-[#f4f3ef] p-[16px]">
      {background === 'launch' ? (
        <img
          src={launchBackground}
          alt=""
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 h-full w-full select-none object-cover object-center"
        />
      ) : null}
      <div
        className="relative overflow-hidden"
        style={{
          height: DESIGN_HEIGHT * scale,
          width: DESIGN_WIDTH * scale,
        }}
      >
        <div
          className="relative h-[1024px] w-[1451px] origin-top-left"
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
