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

  return Math.min(window.innerWidth / DESIGN_WIDTH, window.innerHeight / DESIGN_HEIGHT, 1)
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
    <main className="relative flex h-[100svh] w-screen items-center justify-center overflow-hidden bg-[#f4f3ef]">
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
