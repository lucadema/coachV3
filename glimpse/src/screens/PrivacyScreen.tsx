import radioInactive from '../assets/onboarding/radio-inactive.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

const privacyMessage = `Aether is a confidential thinking space.

The thoughts you share with us
during this session are used solely to
guide your coaching conversation.

It is not stored beyond your active
session, not shared with any third party,
and not used to train AI models.

You are in control of what you share.
Take your time. Think clearly.`

const acknowledgementMessage = `I understand that my session content is confidential,
used only to facilitate this coaching conversation, and
handled in accordance with Aether’s privacy policy.`

type PrivacyScreenProps = {
  hasAcknowledged: boolean
  onAcknowledgedChange: (value: boolean) => void
  onContinue: () => void
}

export function PrivacyScreen({
  hasAcknowledged,
  onAcknowledgedChange,
  onContinue,
}: PrivacyScreenProps) {
  return (
    <OnboardingFrame>
      <div className="absolute inset-[16.6%_26.46%_16.7%_26.46%] rounded-[40px] border-[6px] border-[rgba(41,71,68,0.07)] bg-[rgba(255,255,255,0.5)]" />
      <p className="absolute inset-[26.66%_36.8%_44.04%_36.8%] m-0 whitespace-pre-line text-center text-[20px] font-light leading-[1.18] tracking-[-0.8px] text-[#294744]">
        {privacyMessage}
      </p>
      <label className="absolute inset-[66.7%_40.11%_28.13%_40.25%] flex cursor-pointer items-start gap-[10px] text-[#294744]">
        <input
          type="checkbox"
          checked={hasAcknowledged}
          onChange={(event) => {
            onAcknowledgedChange(event.target.checked)
          }}
          className="sr-only"
        />
        <span className="relative mt-[2px] h-[14px] w-[14px] shrink-0">
          {hasAcknowledged ? (
            <>
              <span
                aria-hidden="true"
                className="absolute inset-0 rounded-full bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]"
              />
              <svg
                viewBox="0 0 14 14"
                aria-hidden="true"
                className="absolute inset-0 h-full w-full"
              >
                <path
                  d="M4 7.4L6.1 9.45L10 4.95"
                  fill="none"
                  stroke="#ffffff"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.6"
                />
              </svg>
            </>
          ) : null}
          <img
            src={radioInactive}
            alt=""
            aria-hidden="true"
            className="absolute inset-0 h-full w-full"
          />
        </span>
        <span className="whitespace-pre-line text-[11px] font-light leading-[1.18] tracking-[-0.44px]">
          {acknowledgementMessage}
        </span>
      </label>
      <div className="absolute inset-[75.1%_44.11%_20.8%_44.18%]">
        <OnboardingButton disabled={!hasAcknowledged} label="Next" onClick={onContinue} />
      </div>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
    </OnboardingFrame>
  )
}
