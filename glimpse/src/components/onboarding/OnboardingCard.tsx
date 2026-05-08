type OnboardingCardProps = {
  className?: string
}

export function OnboardingCard({ className }: OnboardingCardProps) {
  const resolvedClassName = [
    'absolute rounded-[40px] border-[6px] border-[rgba(41,71,68,0.07)] bg-[rgba(255,255,255,0.5)]',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return <div className={resolvedClassName} />
}
