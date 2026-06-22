export function SelectionDot({ selected }: { selected: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={[
        'inline-block size-[18px] shrink-0 rounded-full border-[1.5px] border-[#75b83b] bg-white shadow-[0_0_0_2px_rgba(255,255,255,0.65)]',
        selected ? 'bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]' : 'bg-white',
      ].join(' ')}
    />
  )
}
