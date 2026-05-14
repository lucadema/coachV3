import { MobileButton, MobileFrame, MobileFullCard, MobileSelectionDot, MobileWatermark } from './MobilePrimitives'

type MobilePrivacyScreenProps = {
  hasAcknowledged: boolean
  onAcknowledgedChange: (value: boolean) => void
  onContinue: () => void
}

export function MobilePrivacyScreen({
  hasAcknowledged,
  onAcknowledgedChange,
  onContinue,
}: MobilePrivacyScreenProps) {
  return (
    <MobileFrame label="Aether Glimpse mobile confidentiality">
      <MobileWatermark />
      <MobileFullCard>
        <div className="absolute left-[22px] top-[101px] w-[310px] text-center text-[18px] font-light leading-none tracking-[-0.72px]">
          <p className="m-0">Aether is a confidential thinking space.</p>
          <p className="m-0 mt-[29px]">The thoughts you share with us</p>
          <p className="m-0">during this session are used solely to</p>
          <p className="m-0">guide your coaching conversation.</p>
          <p className="m-0 mt-[29px]">It is not stored beyond your active</p>
          <p className="m-0">session, not shared with any third party,</p>
          <p className="m-0">and not used to train AI models.</p>
          <p className="m-0 mt-[29px]">You are in control of what you share.</p>
          <p className="m-0">Take your time. Think clearly.</p>
        </div>
        <label className="absolute left-[38px] top-[604px] flex cursor-pointer items-start gap-[10px] text-[#294744]">
          <input
            type="checkbox"
            checked={hasAcknowledged}
            onChange={(event) => {
              onAcknowledgedChange(event.target.checked)
            }}
            className="sr-only"
          />
          <MobileSelectionDot selected={hasAcknowledged} />
          <span className="w-[262px] text-[11px] font-light leading-none tracking-[-0.44px]">
            I understand that my session content is confidential, used only to facilitate this coaching conversation, and handled in accordance with Aether’s privacy policy.
          </span>
        </label>
      </MobileFullCard>
      <MobileButton disabled={!hasAcknowledged} label="Next" onClick={onContinue} />
    </MobileFrame>
  )
}
