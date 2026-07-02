# Input Safety Gate

## Purpose

The input safety gate is a deterministic, backend-only pre-check for user
messages before they enter the existing evaluation and coaching flow.

It is intended to block obvious unsafe, unsuitable, or prompt-injection-style
messages without adding another LLM call.

## What It Does

- Blocks empty input, excessive length, repeated-character spam, and repeated
  phrase spam.
- Checks a small configurable set of regex or phrase-level patterns.
- Supports categories such as prompt injection, abusive language, threats,
  sexual content, self-harm or crisis language, illegal or malicious requests,
  system prompt extraction, and spam.
- Returns a structured safety result with a safe user-facing message.

## What It Does Not Do

- It does not perform contextual moderation.
- It does not decide whether a workplace issue is valid for coaching.
- It does not replace the existing LLM evaluation stage.
- It does not alter coaching prompts, evaluation prompts, synthesis, pathways,
  or stage-transition logic for allowed messages.

Contextual coaching relevance remains part of the existing LLM evaluation
stage.

## Enable Or Disable

Configuration lives in `config/input_safety.yaml`.

Supported modes:

- `off`: do not run checks; always allow.
- `monitor`: run checks and report matches internally, but do not block.
- `block`: block when a blocking rule matches.

The environment variable `GLIMPSE_INPUT_SAFETY_MODE` overrides YAML when set to
`off`, `monitor`, or `block`.

Default mode is `block`, because this gate is deliberately narrow and runs
before user text reaches the LLM.

## Adding Rules

Add patterns under a category in `config/input_safety.yaml`.

Each category supports:

- `enabled`
- `severity`
- `action`
- `patterns`
- `user_message`

Keep patterns small, phrase-level, and conservative. Prefer exact injection or
unsafe-intent phrases over broad keyword blacklists.

## Blocked API Response

Blocked `/user_message` responses return HTTP 200 with the current unchanged
session view and safety metadata:

```json
{
  "session": {
    "session_id": "...",
    "stage": "classification",
    "state": "evaluating",
    "cancelled": false,
    "completed": false
  },
  "coach_message": "I can't process instructions that try to change how the coaching system works. Please describe the workplace issue you want to reflect on.",
  "message": "I can't process instructions that try to change how the coaching system works. Please describe the workplace issue you want to reflect on.",
  "blocked": true,
  "safety_blocked": true,
  "safety_category": "prompt_injection",
  "safety_reason_code": "prompt_injection_pattern",
  "synthesis": null,
  "pathways": null
}
```

The response does not expose raw matched text or internal rule details.
