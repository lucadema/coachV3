import { useState } from 'react'
import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileFullCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'
import type { PathwayCard } from '../../types/session'

type MobilePathwaysScreenProps = {
  error?: string | null
  isLoading?: boolean
  onContinue: () => void | Promise<void>
  onDownloadPdf: () => void
  pathways: PathwayCard[]
  rawPathwaysText?: string
}

const introText =
  'Based on everything we have explored, here are the resolution pathways available to you. Each one represents a distinct decision. Expand each resolution pathway for more details.'

const downloadNotice =
  'You’re welcome to keep your problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.'

export function MobilePathwaysScreen({
  error = null,
  isLoading = false,
  onContinue,
  onDownloadPdf,
  pathways,
  rawPathwaysText = '',
}: MobilePathwaysScreenProps) {
  const [expandedPathwayIndex, setExpandedPathwayIndex] = useState<number | null>(null)
  const expandedPathway =
    expandedPathwayIndex === null ? null : (pathways[expandedPathwayIndex] ?? null)

  return (
    <MobileFrame label="Aether Glimpse mobile pathways">
      <MobileWatermark />
      <MobileFullCard>
        <MobilePrimaryIcon variant="aether" />
        {expandedPathway ? (
          <article className="absolute left-[7px] top-[100px] h-[628px] w-[340px] rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]">
            <button
              type="button"
              aria-label="Close expanded pathway"
              onClick={() => {
                setExpandedPathwayIndex(null)
              }}
              className="absolute right-[8px] top-[11px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.5)] text-[18px] text-[#75b83b]"
            >
              x
            </button>
            <h1 className="absolute left-[48px] top-[36px] m-0 w-[244px] text-center text-[14px] font-bold leading-none">
              {expandedPathway.title.toUpperCase()}
            </h1>
            <div className="absolute left-[31px] top-[80px] max-h-[500px] w-[278px] overflow-auto">
              <p className="m-0 whitespace-pre-wrap text-center text-[16px] font-light leading-none tracking-[-0.64px]">
                {expandedPathway.body}
              </p>
            </div>
          </article>
        ) : (
          <>
            <p className="absolute left-[21px] top-[99px] m-0 w-[310px] text-center text-[16px] font-light leading-none tracking-[-0.64px]">
              {introText}
            </p>
            <div className="absolute left-[7px] top-[218px] flex w-[340px] flex-col gap-[23px]">
              {(pathways.length > 0 ? pathways : [{ title: rawPathwaysText || 'No pathway details are available yet.', body: '' }])
                .slice(0, 4)
                .map((pathway, index) => (
                  <article
                    key={`${pathway.title}-${index}`}
                    className="relative h-[70px] rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]"
                  >
                    <span aria-hidden="true" className="absolute left-[12px] top-[15px] text-[28px] font-thin text-[rgba(117,184,59,0.35)]">
                      ♡
                    </span>
                    <h2 className="absolute left-[54px] top-1/2 m-0 w-[232px] -translate-y-1/2 text-center text-[14px] font-bold leading-none">
                      {pathway.title.toUpperCase()}
                    </h2>
                    {pathway.body ? (
                      <button
                        type="button"
                        aria-label={`Expand ${pathway.title}`}
                        disabled={isLoading}
                        onClick={() => {
                          setExpandedPathwayIndex(index)
                        }}
                        className="absolute right-[10px] top-[10px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.5)] text-[22px] font-light leading-none text-[#75b83b]"
                      >
                        +
                      </button>
                    ) : null}
                  </article>
                ))}
            </div>
            <button
              type="button"
              aria-label="Download session PDF"
              onClick={onDownloadPdf}
              className="absolute left-[53px] top-[613px] flex size-[22px] items-center justify-center rounded-[8px] border-[1.5px] border-[#dbec03] text-[15px] text-[#75b83b]"
            >
              ↓
            </button>
            <p className="absolute left-[84px] top-[614px] m-0 w-[223px] text-left text-[11px] font-light leading-none tracking-[-0.44px]">
              {downloadNotice}
            </p>
          </>
        )}
      </MobileFullCard>
      {expandedPathway ? null : (
        <MobileButton
          disabled={isLoading}
          label="Continue"
          onClick={() => {
            void onContinue()
          }}
        />
      )}
      <MobileError>{error}</MobileError>
    </MobileFrame>
  )
}
