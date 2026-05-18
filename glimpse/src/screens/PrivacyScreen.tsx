import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
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
      <OnboardingCard className="inset-[16.6%_26.46%_16.7%_26.46%]" />
      <p className="absolute inset-[26.66%_36.8%_44.04%_36.8%] m-0 whitespace-pre-line text-center text-[20px] font-light leading-[1.18] tracking-[-0.8px] text-[#294744]">
        {privacyMessage}
      </p>
      <label className="absolute left-[580px] top-[678px] flex w-[292px] cursor-pointer items-start gap-[12px] text-[#294744]">
        <input
          type="checkbox"
          checked={hasAcknowledged}
          onChange={(event) => {
            onAcknowledgedChange(event.target.checked)
          }}
          className="sr-only"
        />
        <span className="relative mt-[1px] flex size-[18px] shrink-0 items-center justify-center rounded-full border-[1.5px] border-[#75b83b] bg-white shadow-[0_0_0_2px_rgba(255,255,255,0.7)]">
          {hasAcknowledged ? (
            <>
              <span
                aria-hidden="true"
                className="absolute inset-0 rounded-full bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]"
              />
              <svg
                viewBox="0 0 18 18"
                aria-hidden="true"
                className="absolute inset-0 h-full w-full"
              >
                <path
                  d="M5.1 9.2l2.5 2.45 5.2-6"
                  fill="none"
                  stroke="#ffffff"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                />
              </svg>
            </>
          ) : null}
        </span>
        <span className="whitespace-pre-line text-[11px] font-light leading-[1.18] tracking-[-0.44px]">
          {acknowledgementMessage}
        </span>
      </label>
      <div className="absolute inset-[75.1%_44.11%_20.8%_44.18%]">
        <OnboardingButton
          disabled={!hasAcknowledged}
          label="Continue"
          onClick={onContinue}
        />
      </div>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
    </OnboardingFrame>
  )
}
