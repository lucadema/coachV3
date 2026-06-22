import { useCallback, useEffect, useRef, useState } from 'react'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { FeedbackForm } from '../features/feedback/FeedbackForm'
import type { FeedbackFormConfig, FeedbackState } from '../types/feedback'

type FeedbackScreenProps = {
  error?: string | null
  feedback: FeedbackState
  form: FeedbackFormConfig | null
  onChange: (feedback: FeedbackState) => void
  onClose: (feedback: FeedbackState) => void
}

export function FeedbackScreen({
  error = null,
  feedback,
  form,
  onChange,
  onClose,
}: FeedbackScreenProps) {
  const scrollContainerRef = useRef<HTMLDivElement | null>(null)
  const [canScrollUp, setCanScrollUp] = useState(false)
  const [canScrollDown, setCanScrollDown] = useState(false)
  const title =
    form?.title ?? 'Before you go, please tell us what you thought of the Aether Glimpse experience.'

  const updateScrollAffordances = useCallback(() => {
    const container = scrollContainerRef.current

    if (!container) {
      setCanScrollUp(false)
      setCanScrollDown(false)
      return
    }

    const scrollBuffer = 2
    setCanScrollUp(container.scrollTop > scrollBuffer)
    setCanScrollDown(
      container.scrollTop + container.clientHeight < container.scrollHeight - scrollBuffer,
    )
  }, [])

  useEffect(() => {
    updateScrollAffordances()
  }, [form, updateScrollAffordances])

  function handleQuestionExpanded(questionElement: HTMLDivElement | null) {
    const container = scrollContainerRef.current

    if (!container || !questionElement) {
      return
    }

    window.requestAnimationFrame(() => {
      const containerRect = container.getBoundingClientRect()
      const questionRect = questionElement.getBoundingClientRect()
      const bottomPadding = 20
      const topPadding = 12

      const scrollDelta =
        questionRect.bottom > containerRect.bottom - bottomPadding
          ? questionRect.bottom - containerRect.bottom + bottomPadding
          : questionRect.top < containerRect.top + topPadding
            ? questionRect.top - containerRect.top - topPadding
            : 0

      if (scrollDelta !== 0) {
        if (typeof container.scrollBy === 'function') {
          container.scrollBy({
            behavior: 'smooth',
            top: scrollDelta,
          })
        } else {
          container.scrollTop += scrollDelta
        }
      }

      window.setTimeout(updateScrollAffordances, 260)
    })
  }

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-label="Aether Glimpse feedback survey"
        className="absolute left-[405px] top-[150px] h-[718px] w-[640px]"
      >
        <OnboardingCard className="inset-0" />
        <h1 className="absolute left-[20px] top-[38px] m-0 w-[600px] text-center text-[29px] font-light leading-none tracking-[-1.16px] text-[#294744]">
          {title}
        </h1>

        {form?.description ? (
          <p className="absolute left-[64px] top-[105px] m-0 w-[512px] text-center text-[14px] font-light leading-[1.25] text-[#294744]">
            {form.description}
          </p>
        ) : null}

        <div className="absolute left-[20px] top-[163px] h-[430px] w-[600px]">
          <div
            ref={scrollContainerRef}
            data-feedback-scroll-container
            onScroll={updateScrollAffordances}
            style={{
              scrollbarColor: '#75b83b rgba(117,184,59,0.16)',
              scrollbarGutter: 'stable',
              scrollbarWidth: 'thin',
            }}
            className="feedback-scrollbar flex h-full flex-col gap-[54px] overflow-y-auto pr-[14px] text-[#294744] [&_.feedback-question:nth-child(3)]:mt-[-10px] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#75b83b] [&::-webkit-scrollbar-track]:rounded-full [&::-webkit-scrollbar-track]:bg-[rgba(117,184,59,0.16)] [&::-webkit-scrollbar]:w-[10px]"
          >
            {form?.show_feedback ? (
              <FeedbackForm
                feedback={feedback}
                form={form}
                onChange={onChange}
                onQuestionExpanded={handleQuestionExpanded}
              />
            ) : null}
          </div>

          {canScrollUp ? (
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[34px] bg-[linear-gradient(180deg,rgba(247,250,238,0.98)_0%,rgba(247,250,238,0)_100%)]" />
          ) : null}

          {canScrollDown ? (
            <div className="pointer-events-none absolute inset-x-0 bottom-0 flex h-[52px] items-end justify-center bg-[linear-gradient(0deg,rgba(247,250,238,0.98)_0%,rgba(247,250,238,0)_100%)] pb-[2px]">
              <span className="rounded-full bg-[rgba(255,255,255,0.78)] px-[12px] py-[4px] text-[11px] font-normal uppercase tracking-[0.8px] text-[#527c3a] shadow-[0_2px_8px_rgba(41,71,68,0.08)]">
                More below
              </span>
            </div>
          ) : null}
        </div>

        {error ? (
          <p
            role="alert"
            className="absolute left-[70px] top-[662px] m-0 w-[500px] text-center text-[13px] font-light leading-[1.2] text-[#294744]"
          >
            {error}
          </p>
        ) : null}

        <div className="absolute left-[235px] top-[636px]">
          <OnboardingButton
            label="Continue"
            onClick={() => {
              onClose(feedback)
            }}
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
