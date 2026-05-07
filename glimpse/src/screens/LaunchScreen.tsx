import launchBackground from '../assets/launch/launch-background.jpg'
import aetherWordmark from '../assets/launch/aether-wordmark.svg'

export function LaunchScreen() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f4f3ef]">
      <img
        src={launchBackground}
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full select-none object-cover object-center"
      />
      <img
        src={aetherWordmark}
        alt="Aether"
        className="relative z-10 w-[clamp(16rem,48.84vw,44.29375rem)] max-w-[calc(100vw-3rem)] select-none"
      />
    </main>
  )
}
