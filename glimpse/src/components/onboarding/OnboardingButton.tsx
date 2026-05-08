type OnboardingButtonTone = 'filled' | 'outline'

type OnboardingButtonProps = {
  disabled?: boolean
  label: string
  onClick: () => void
  tone?: OnboardingButtonTone
}

export function OnboardingButton({
  disabled = false,
  label,
  onClick,
  tone,
}: OnboardingButtonProps) {
  const resolvedTone = tone ?? (disabled ? 'outline' : 'filled')

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        'flex h-[42px] w-[170px] items-center justify-center rounded-[16px] border-[1.5px] border-[#dbec03] text-center text-[17px] font-bold leading-none',
        disabled ? 'cursor-not-allowed' : 'cursor-pointer',
        resolvedTone === 'filled'
          ? 'bg-[linear-gradient(90deg,#dbec03_0%,#75b83b_100%)] text-white'
          : 'bg-transparent text-[rgba(41,71,68,0.5)]',
      ].join(' ')}
    >
      <span className="translate-y-[-0.5px]">{label}</span>
    </button>
  )
}
