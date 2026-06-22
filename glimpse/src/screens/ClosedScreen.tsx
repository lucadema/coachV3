import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { DownloadIcon } from '../components/onboarding/UiIcons'

type ClosedScreenProps = {
  onDownloadPdf: () => void
  onStartNewSession: () => void
}

const downloadNotice =
  'Keep a record by downloading the problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.'

export function ClosedScreen({ onDownloadPdf, onStartNewSession }: ClosedScreenProps) {
  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
      <section aria-label="Aether session closed">
        <h1 className="absolute left-[92px] top-[285px] m-0 w-[1260px] text-center text-[78px] font-thin leading-[78px] tracking-[-3.12px] text-[#294744]">
          We hope you’ve enjoyed this glimpse of Aether
        </h1>
        <p className="absolute left-[182px] top-[430px] m-0 w-[1080px] text-center text-[78px] font-thin leading-[78px] tracking-[-3.12px] text-[#294744]">
          Feel free to download a copy of your session and to start a new one.
        </p>
        <div className="absolute left-1/2 top-[615px] flex w-[520px] -translate-x-1/2 items-start justify-center gap-[13px]">
          <button
            type="button"
            aria-label="Download session PDF"
            onClick={onDownloadPdf}
            className="flex size-[30px] shrink-0 cursor-pointer items-center justify-center rounded-[10px] border-[1.5px] border-[#dbec03] bg-transparent text-[#75b83b]"
          >
            <DownloadIcon />
          </button>
          <p className="m-0 w-[460px] text-left text-[11px] font-light leading-none tracking-[-0.44px] text-[#294744]">
            {downloadNotice}
          </p>
        </div>
        <div className="absolute left-1/2 top-[703px] -translate-x-1/2">
          <OnboardingButton
            label="Start New Session"
            onClick={onStartNewSession}
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
