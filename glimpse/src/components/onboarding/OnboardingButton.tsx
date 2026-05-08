type OnboardingButtonProps = {
  disabled?: boolean
  label: string
  onClick: () => void
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
        'flex h-[42px] w-[170px] items-center justify-center rounded-[16px] border-[1.5px] border-[#dbec03] text-center text-[17px] font-bold leading-none',
        disabled
          ? 'cursor-not-allowed bg-transparent text-[rgba(41,71,68,0.5)]'
          : 'cursor-pointer bg-[linear-gradient(90deg,#dbec03_0%,#75b83b_100%)] text-white',
      ].join(' ')}
    >
      <span className="translate-y-[-0.5px]">{label}</span>
    </button>
  )
}
