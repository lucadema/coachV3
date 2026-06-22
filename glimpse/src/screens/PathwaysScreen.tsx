import { useState } from 'react'
import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { CloseIcon, DownloadIcon, ExpandIcon, HeartIcon } from '../components/onboarding/UiIcons'
import type { PathwayCard } from '../types/session'

type PathwaysScreenProps = {
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
  'Based on everything we have explored, here are the resolution pathways available to you. Each one represents a distinct decision. Expand each resolution pathway for more details'

const downloadNotice =
  'You’re welcome to keep your problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.'

function ExpandButton({
  disabled,
  onClick,
  title,
}: {
  disabled?: boolean
  onClick: () => void
  title: string
}) {
  return (
    <button
      type="button"
      aria-label={`Expand ${title}`}
      disabled={disabled}
      onClick={onClick}
      className="absolute right-[7px] top-[7px] flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b] disabled:cursor-wait"
    >
      <ExpandIcon />
    </button>
  )
}

function CloseButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label="Close expanded pathway"
      onClick={onClick}
      className="absolute right-[7px] top-[7px] flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]"
    >
      <CloseIcon />
    </button>
  )
}

function DownloadButton({ onDownloadPdf }: { onDownloadPdf: () => void }) {
  return (
    <button
      type="button"
      aria-label="Download session PDF"
      onClick={onDownloadPdf}
      className="absolute left-[39px] top-[588px] flex size-[30px] cursor-pointer items-center justify-center rounded-[10px] border-[1.5px] border-[#dbec03] bg-transparent text-[#75b83b]"
    >
      <DownloadIcon />
    </button>
  )
}

function ExpandedPathwayBody({ body }: { body: string }) {
  const sectionMatch = body.match(/Orientation:\s*([\s\S]*?)(?:\n\s*)?Conditions:\s*([\s\S]*)/i)

  if (!sectionMatch) {
    return (
      <p className="m-0 whitespace-pre-wrap text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]">
        {body}
      </p>
    )
  }

  const [, orientation, conditions] = sectionMatch

  return (
    <div className="text-center text-[20px] leading-[1.18] tracking-[-0.8px] text-[#294744]">
      <h2 className="m-0 text-[20px] font-normal leading-[1.18]">Orientation:</h2>
      <p className="m-0 whitespace-pre-wrap font-light leading-[1.18]">{orientation.trim()}</p>
      <h2 className="m-0 mt-[28px] text-[20px] font-normal leading-[1.18]">Conditions:</h2>
      <p className="m-0 whitespace-pre-wrap font-light leading-[1.18]">{conditions.trim()}</p>
    </div>
  )
}

function PathwaySummaryCard({
  index,
  isLoading,
  isSelected,
  pathway,
  onExpand,
  onSelect,
}: {
  index: number
  isLoading: boolean
  isSelected: boolean
  onExpand: (index: number) => void
  onSelect: (pathway: PathwayCard) => void
  pathway: PathwayCard
}) {
  return (
    <article className="relative h-[97px] w-[288px] rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]">
      <h2 className="absolute left-[26px] top-1/2 m-0 w-[236px] -translate-y-1/2 text-center text-[15px] font-bold leading-none text-[#294744]">
        {pathway.title.toUpperCase()}
      </h2>
      <button
        type="button"
        aria-pressed={isSelected}
        aria-label={`${isSelected ? 'Unheart' : 'Heart'} ${pathway.title}`}
        disabled={isLoading}
        onClick={() => {
          onSelect(pathway)
        }}
        className={[
          'absolute left-[7px] top-[7px] flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] disabled:cursor-wait',
          isSelected ? 'text-[#75b83b]' : 'text-[rgba(41,71,68,0.45)]',
        ].join(' ')}
      >
        <HeartIcon filled={isSelected} />
      </button>
      <ExpandButton
        disabled={isLoading}
        title={pathway.title}
        onClick={() => {
          onExpand(index)
        }}
      />
    </article>
  )
}

function RawFallback({ text }: { text: string }) {
  return (
    <div className="absolute left-[20px] top-[325px] h-[219px] w-[600px] overflow-auto rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)] px-[32px] py-[28px]">
      <p className="m-0 whitespace-pre-wrap text-center text-[17px] font-light leading-[1.25] tracking-[-0.68px] text-[#294744]">
        {text || 'No pathway details are available yet.'}
      </p>
    </div>
  )
}

export function PathwaysScreen({
  error = null,
  isLoading = false,
  onContinue,
  onDownloadPdf,
  onSelectPathway,
  pathways,
  rawPathwaysText = '',
  selectedPathwayTitle = null,
}: PathwaysScreenProps) {
  const [expandedPathwayIndex, setExpandedPathwayIndex] = useState<number | null>(null)
  const expandedPathway =
    expandedPathwayIndex === null ? null : (pathways[expandedPathwayIndex] ?? null)
  const hasPathwayCards = pathways.length > 0

  async function handleContinue() {
    if (isLoading) {
      return
    }

    await onContinue()
  }

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-busy={isLoading}
        aria-label={expandedPathway ? 'Expanded pathway' : 'Pathway options'}
        className="absolute left-[405px] top-[170px] h-[683px] w-[640px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconAetherCoach}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[45px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />

        {expandedPathway ? (
          <div className="absolute left-[20px] top-[124px] h-[517px] w-[600px] rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]">
            <CloseButton
              onClick={() => {
                setExpandedPathwayIndex(null)
              }}
            />
            <h1 className="absolute left-[60px] top-[32px] m-0 w-[480px] text-center text-[15px] font-bold leading-none text-[#294744]">
              {expandedPathway.title.toUpperCase()}
            </h1>
            <div className="absolute left-[36px] top-[84px] max-h-[382px] w-[528px] overflow-auto">
              <ExpandedPathwayBody body={expandedPathway.body} />
            </div>
          </div>
        ) : (
          <>
            <p className="absolute left-[20px] top-[146px] m-0 w-[600px] text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]">
              {introText}
            </p>

            {hasPathwayCards ? (
              <div className="absolute left-[19px] top-[325px] grid grid-cols-2 gap-x-[25px] gap-y-[25px]">
                {pathways.slice(0, 4).map((pathway, index) => (
                  <PathwaySummaryCard
                    index={index}
                    isSelected={selectedPathwayTitle === pathway.title}
                    isLoading={isLoading}
                    key={`${pathway.title}-${index}`}
                    pathway={pathway}
                    onExpand={setExpandedPathwayIndex}
                    onSelect={(selectedPathway) => {
                      onSelectPathway?.(selectedPathway)
                    }}
                  />
                ))}
              </div>
            ) : (
              <RawFallback text={rawPathwaysText} />
            )}

            <DownloadButton onDownloadPdf={onDownloadPdf} />
            <p className="absolute left-[75px] top-[592px] m-0 w-[222px] text-left text-[11px] font-light leading-none tracking-[-0.44px] text-[#294744]">
              {downloadNotice}
            </p>
            <div className="absolute left-[390px] top-[598px]">
              <OnboardingButton
                disabled={isLoading}
                label="Continue"
                onClick={() => {
                  void handleContinue()
                }}
              />
            </div>
          </>
        )}

        {error ? (
          <p
            role="alert"
            className="absolute left-[92px] top-[652px] m-0 w-[500px] text-center text-[13px] font-light leading-[1.2] text-[#294744]"
          >
            {error}
          </p>
        ) : null}
      </section>
    </OnboardingFrame>
  )
}
