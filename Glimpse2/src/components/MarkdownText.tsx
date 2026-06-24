type MarkdownTextProps = {
  text: string
}

export function MarkdownText({ text }: MarkdownTextProps) {
  const blocks = text.trim().split(/\n{2,}/).filter(Boolean)

  if (blocks.length === 0) {
    return null
  }

  return (
    <div className="markdown-text">
      {blocks.map((block) => {
        if (block.startsWith('## ')) {
          return <h3 key={block}>{block.replace(/^##\s+/, '')}</h3>
        }

        if (/^[-*]\s+/m.test(block)) {
          return (
            <ul key={block}>
              {block
                .split(/\n/)
                .map((line) => line.replace(/^[-*]\s+/, '').trim())
                .filter(Boolean)
                .map((line) => (
                  <li key={line}>{line}</li>
                ))}
            </ul>
          )
        }

        return <p key={block}>{block}</p>
      })}
    </div>
  )
}
