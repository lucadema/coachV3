import { useState } from 'react'
import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileFullCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'
import { CloseIcon, DownloadIcon, ExpandIcon, HeartIcon } from '../../components/onboarding/UiIcons'
import type { PathwayCard } from '../../types/session'

type MobilePathwaysScreenProps = {
  error?: string | null
  isLoading?: boolean
  onContinue: () => void | Promise<void>
  onDownloadPdf: () => void
  onSelectPathway?: (pathway: PathwayCard) => void
  pathways: PathwayCard[]
  rawPathwaysText?: string
  selectedPathwayTitle?: string | null
}

const introText =
  'Based on everything we have explored, here are the resolution pathways available to you. Each one represents a distinct decision. Expand each resolution pathway for more details.'

const downloadNotice =
  'You’re welcome to keep your problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.'

function MobileExpandedPathwayBody({ body }: { body: string }) {
  const sectionMatch = body.match(/Orientation:\s*([\s\S]*?)(?:\n\s*)?Conditions:\s*([\s\S]*)/i)

  if (!sectionMatch) {
    return (
      <p className="m-0 whitespace-pre-wrap text-center text-[16px] font-light leading-none tracking-[-0.64px]">
        {body}
      </p>
    )
  }

  const [, orientation, conditions] = sectionMatch

  return (
    <div className="text-center text-[16px] leading-[1.18] tracking-[-0.64px]">
      <h2 className="m-0 text-[16px] font-normal leading-[1.18]">Orientation:</h2>
      <p className="m-0 whitespace-pre-wrap font-light leading-[1.18]">{orientation.trim()}</p>
      <h2 className="m-0 mt-[24px] text-[16px] font-normal leading-[1.18]">Conditions:</h2>
      <p className="m-0 whitespace-pre-wrap font-light leading-[1.18]">{conditions.trim()}</p>
    </div>
  )
}

export function MobilePathwaysScreen({
  error = null,
  isLoading = false,
  onContinue,
  onDownloadPdf,
  onSelectPathway,
  pathways,
  rawPathwaysText = '',
  selectedPathwayTitle = null,
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
          <article className="absolute left-[22px] top-[100px] h-[628px] w-[310px] rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]">
            <button
              type="button"
              aria-label="Close expanded pathway"
              onClick={() => {
                setExpandedPathwayIndex(null)
              }}
              className="absolute right-[2px] top-[5px] flex size-[34px] items-center justify-center p-[5px] text-[#75b83b]"
            >
              <span className="flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)]">
                <CloseIcon />
              </span>
            </button>
            <h1 className="absolute left-[33px] top-[36px] m-0 w-[244px] text-center text-[14px] font-bold leading-none">
              {expandedPathway.title.toUpperCase()}
            </h1>
            <div className="absolute left-[22px] top-[80px] max-h-[500px] w-[266px] overflow-auto">
              <MobileExpandedPathwayBody body={expandedPathway.body} />
            </div>
          </article>
        ) : (
          <>
            <p className="absolute left-[21px] top-[99px] m-0 w-[310px] text-center text-[16px] font-light leading-none tracking-[-0.64px]">
              {introText}
            </p>
            <div className="absolute left-[22px] top-[218px] flex w-[310px] flex-col gap-[23px]">
              {(pathways.length > 0 ? pathways : [{ title: rawPathwaysText || 'No pathway details are available yet.', body: '' }])
                .slice(0, 4)
                .map((pathway, index) => (
                  <div
                    key={`${pathway.title}-${index}`}
                    className="relative h-[70px] rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]"
                  >
                    {pathway.body ? (
                      <button
                        type="button"
                        aria-pressed={selectedPathwayTitle === pathway.title}
                        aria-label={`${selectedPathwayTitle === pathway.title ? 'Unheart' : 'Heart'} ${pathway.title}`}
                        disabled={isLoading}
                        onClick={() => {
                          onSelectPathway?.(pathway)
                        }}
                        className={[
                          'absolute left-[10px] top-[10px] z-10 flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] disabled:cursor-wait',
                          selectedPathwayTitle === pathway.title
                            ? 'text-[#75b83b]'
                            : 'text-[rgba(41,71,68,0.45)]',
                        ].join(' ')}
                      >
                        <HeartIcon filled={selectedPathwayTitle === pathway.title} />
                      </button>
                    ) : null}
                    {pathway.body ? (
                      <button
                        type="button"
                        aria-label={`Expand ${pathway.title}`}
                        disabled={isLoading}
                        onClick={() => {
                          setExpandedPathwayIndex(index)
                        }}
                        className="absolute inset-0 flex items-center justify-center rounded-[24px] px-[38px] text-center text-[14px] font-bold leading-none disabled:cursor-wait"
                      >
                        {pathway.title.toUpperCase()}
                        <span className="absolute right-[10px] top-[10px] flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]">
                          <ExpandIcon />
                        </span>
                      </button>
                    ) : (
                      <h2 className="absolute inset-x-[34px] top-1/2 m-0 -translate-y-1/2 text-center text-[14px] font-bold leading-none">
                        {pathway.title.toUpperCase()}
                      </h2>
                    )}
                  </div>
                ))}
            </div>
            <button
              type="button"
              aria-label="Download session PDF"
              onClick={onDownloadPdf}
              className="absolute left-[53px] top-[613px] flex size-[24px] items-center justify-center rounded-[8px] border-[1.5px] border-[#dbec03] text-[#75b83b]"
            >
              <DownloadIcon className="size-[16px]" />
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
