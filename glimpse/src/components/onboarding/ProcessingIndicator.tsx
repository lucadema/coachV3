export function ProcessingIndicator({ label = 'Processing...' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-[9px] text-[13px] font-light leading-none tracking-[-0.52px] text-[#294744]"
    >
      <span
        aria-hidden="true"
        className="size-[13px] animate-spin rounded-full border-[1.5px] border-[rgba(117,184,59,0.25)] border-t-[#75b83b]"
      />
      <span>{label}</span>
    </div>
  )
}
