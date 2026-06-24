import { MobileButton, MobileFrame, MobileWatermark } from './MobilePrimitives'
import { DownloadIcon } from '../../components/onboarding/UiIcons'

type MobileClosedScreenProps = {
  onDownloadPdf: () => void
  onStartNewSession: () => void
}

const downloadNotice =
  'Keep a record by downloading the problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.'

export function MobileClosedScreen({ onDownloadPdf, onStartNewSession }: MobileClosedScreenProps) {
  return (
    <MobileFrame label="Aether Glimpse mobile closed">
      <MobileWatermark />
      <h1 className="absolute left-[25px] top-[206px] m-0 w-[340px] text-center text-[30px] font-thin leading-[34px] tracking-[-1.2px]">
        We hope you’ve enjoyed this glimpse of Aether
      </h1>
      <p className="absolute left-[25px] top-[378px] m-0 w-[340px] text-center text-[24px] font-thin leading-[29px] tracking-[-0.96px]">
        Feel free to download a copy of your session and to start a new one.
      </p>
      <div className="absolute left-1/2 top-[626px] flex w-[340px] -translate-x-1/2 items-start justify-center gap-[10px]">
        <button
          type="button"
          aria-label="Download session PDF"
          onClick={onDownloadPdf}
          className="flex size-[24px] shrink-0 items-center justify-center rounded-[8px] border-[1.5px] border-[#dbec03] text-[#75b83b]"
        >
          <DownloadIcon className="size-[16px]" />
        </button>
        <p className="m-0 w-[306px] text-left text-[16.5px] font-light leading-[18px] tracking-[-0.66px]">
          {downloadNotice}
        </p>
      </div>
      <MobileButton label="Start New Session" onClick={onStartNewSession} top={766} />
    </MobileFrame>
  )
}
