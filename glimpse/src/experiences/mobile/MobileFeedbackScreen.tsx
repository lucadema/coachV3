import { MobileButton, MobileFrame, MobileFullCard, MobilePrimaryIcon, MobileWatermark } from './MobilePrimitives'
import { FeedbackForm } from '../../features/feedback/FeedbackForm'
import type { FeedbackFormConfig, FeedbackState } from '../../types/feedback'

type MobileFeedbackScreenProps = {
  feedback: FeedbackState
  form: FeedbackFormConfig | null
  onChange: (feedback: FeedbackState) => void
  onClose: (feedback: FeedbackState) => void
}

export function MobileFeedbackScreen({
  feedback,
  form,
  onChange,
  onClose,
}: MobileFeedbackScreenProps) {
  const title =
    form?.title ?? 'Before you go, please tell us what you thought of the Aether Glimpse experience.'

  return (
    <MobileFrame label="Aether Glimpse mobile survey">
      <MobileWatermark />
      <MobileFullCard>
        <MobilePrimaryIcon variant="aether" />
        <p className="absolute inset-x-[22px] top-[92px] m-0 text-center text-[16px] font-medium leading-none tracking-[-0.64px] break-words">
          Thank you. We’ve now completed the session. You’ve clarified the core tension well, and have several resolution pathways you can action.
        </p>
        <p className="absolute inset-x-[22px] top-[176px] m-0 text-center text-[16px] font-medium leading-none tracking-[-0.64px] break-words">
          {title}
        </p>
        <div className="absolute inset-x-[22px] top-[266px] flex max-h-[360px] min-w-0 flex-col gap-[46px] overflow-x-hidden overflow-y-auto pb-[16px] text-[#294744] [&_.feedback-question:nth-child(3)]:mt-[-10px]">
          {form?.show_feedback ? (
            <FeedbackForm feedback={feedback} form={form} onChange={onChange} />
          ) : null}
        </div>
      </MobileFullCard>
      <MobileButton
        label="Continue"
        onClick={() => {
          onClose(feedback)
        }}
      />
    </MobileFrame>
  )
}
