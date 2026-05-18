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
}: OnboardingButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        'flex h-[42px] w-[170px] items-center justify-center rounded-[16px] border-[1.5px] border-[#dbec03] bg-transparent text-center text-[17px] font-bold leading-none text-[rgba(41,71,68,0.5)] transition-colors duration-100 active:bg-[linear-gradient(90deg,#dbec03_0%,#75b83b_100%)] active:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#75b83b]',
        disabled ? 'cursor-not-allowed' : 'cursor-pointer',
      ].join(' ')}
    >
      <span className="translate-y-[-0.5px]">{label}</span>
    </button>
  )
}
