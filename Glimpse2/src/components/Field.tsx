import { useState, type FormEvent } from 'react'
import { Button } from './Button'

type PromptFormProps = {
  buttonLabel: string
  disabled?: boolean
  initialValue?: string
  minRows?: number
  placeholder: string
  onSubmit: (value: string) => void
}

export function PromptForm({
  buttonLabel,
  disabled = false,
  initialValue = '',
  minRows = 5,
  placeholder,
  onSubmit,
}: PromptFormProps) {
  const [value, setValue] = useState(initialValue)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedValue = value.trim()

    if (!trimmedValue || disabled) {
      return
    }

    onSubmit(trimmedValue)
    setValue('')
  }

  return (
    <form className="prompt-form" onSubmit={handleSubmit}>
      <textarea
        className="text-area"
        disabled={disabled}
        onChange={(event) => setValue(event.target.value)}
        placeholder={placeholder}
        rows={minRows}
        value={value}
      />
      <div className="form-actions">
        <Button disabled={disabled || !value.trim()} type="submit">
          {buttonLabel}
        </Button>
      </div>
    </form>
  )
}
