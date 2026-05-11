import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import type { BackendSessionView, FrontendScreen } from '../types/session'

type BackendResponsePlaceholderProps = {
  coachMessage: string
  error?: string | null
  previousScreen?: FrontendScreen | null
  resolvedScreen: FrontendScreen | null
  sessionView: BackendSessionView | null
  stayedInCoaching?: boolean | null
}

export function BackendResponsePlaceholder({
  coachMessage,
  error = null,
  previousScreen = null,
  resolvedScreen,
  sessionView,
  stayedInCoaching = null,
}: BackendResponsePlaceholderProps) {
  return (
    <OnboardingFrame background="plain">
      <section className="absolute left-[333px] top-[170px] h-[684px] w-[785px]">
        <OnboardingCard className="inset-0" />
        <div className="absolute inset-[58px_72px] flex flex-col gap-[24px] text-[#294744]">
          <div className="text-center">
            <p className="m-0 text-[13px] font-bold uppercase leading-none tracking-[1.6px] text-[rgba(41,71,68,0.45)]">
              Backend response placeholder
            </p>
            <h1 className="m-0 mt-[14px] text-[28px] font-light leading-[1.1]">
              Backend response received
            </h1>
            <p className="m-0 mt-[10px] text-[15px] font-light leading-[1.35] text-[rgba(41,71,68,0.72)]">
              The resolved target screen is intentionally not implemented yet.
            </p>
          </div>

          {error ? (
            <p
              role="alert"
              className="m-0 rounded-[18px] border border-[#dbec03] px-[18px] py-[12px] text-[14px] leading-[1.35]"
            >
              {error}
            </p>
          ) : null}

          <dl className="m-0 grid grid-cols-[180px_1fr] gap-x-[18px] gap-y-[12px] text-[16px] leading-[1.35]">
            <dt className="font-bold">Previous screen</dt>
            <dd className="m-0">{previousScreen ?? 'Not recorded'}</dd>

            <dt className="font-bold">Resolved next screen</dt>
            <dd className="m-0">{resolvedScreen ?? 'Not resolved yet'}</dd>

            <dt className="font-bold">Backend stage</dt>
            <dd className="m-0">{String(sessionView?.stage ?? 'Not returned')}</dd>

            <dt className="font-bold">Backend state</dt>
            <dd className="m-0">{String(sessionView?.state ?? 'Not returned')}</dd>

            <dt className="font-bold">Stayed in coaching</dt>
            <dd className="m-0">
              {stayedInCoaching === null ? 'Not recorded' : stayedInCoaching ? 'Yes' : 'No'}
            </dd>
          </dl>

          <div>
            <h2 className="m-0 text-[17px] font-bold leading-none">coach_message</h2>
            <div className="mt-[12px] max-h-[320px] overflow-auto rounded-[24px] border border-[rgba(41,71,68,0.12)] bg-[rgba(255,255,255,0.42)] p-[22px]">
              <p className="m-0 whitespace-pre-wrap text-[17px] font-light leading-[1.45]">
                {coachMessage || 'No coach_message returned.'}
              </p>
            </div>
          </div>
        </div>
      </section>
    </OnboardingFrame>
  )
}
