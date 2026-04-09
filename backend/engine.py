"""
LLM interaction and prompt assembly for Coach V3.

Public API
----------
Callers should use only:
- evaluate(...)
- coach(...)

Engine responsibility
---------------------
The engine is intentionally a thin LLM/prompt boundary. It:
- loads a stage YAML file
- concatenates YAML text fragments in the fixed V3 order
- appends runtime payload after the fixed YAML text
- optionally calls the LLM
- extracts structured JSON output when requested
- adds explicit debug lines that make prompt/config/LLM behavior traceable

What this module does not own
-----------------------------
The engine does not own:
- macro-stage transitions
- stage-local FSM transitions
- business decisions about whether a session advances, cancels, or completes
- persistence or session retrieval

High-level flow
---------------
evaluate(...) / coach(...)
    -> _load_stage_config(...)
    -> _assemble_prompt(...)
    -> _append_runtime_context(...)
    -> _call_llm(...)
    -> _extract_output(...) when raw LLM output is available
    -> _with_debug(...)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml


LLM_ENABLED_VALUES = {"1", "true", "yes", "on"}
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


# ============================================================================
# YAML Loading And Text Assembly
# ============================================================================

def _load_stage_config(path: str | Path) -> dict[str, Any]:
    """
    Load one stage YAML file and return the raw mapping.

    The engine expects each stage file to follow the V3 template shape:
    - meta
    - common
    - stage
    - states

    This helper does not validate the semantic meaning of those sections. YAML
    remains a prompt text asset, not a control-flow asset.
    """
    stage_config_path = Path(path)

    with stage_config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError(f"YAML root must be a mapping: {stage_config_path}")

    return config


def _get_text(section: dict[str, Any], key: str) -> str:
    """
    Return text from a YAML section without interpreting its meaning.

    Lists are flattened into newline-separated text so YAML authors can choose
    either block strings or simple lists for prompt fragments.
    """
    value = section.get(key)

    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if item is not None)

    return str(value).strip()


def _assemble_prompt(
    config: dict[str, Any],
    state_name: str,
    interaction_type: str,
) -> str:
    """
    Assemble YAML text in the exact V3 order for one interaction type.

    Description fields are intentionally ignored.

    Evaluation order:
    1. common.preamble
    2. common.role
    3. common.rules
    4. common.output_spec
    5. stage.purpose
    6. stage.rules
    7. stage.evaluation
    8. states.<state>.purpose
    9. states.<state>.evaluation

    Coaching uses the same order, replacing evaluation with coaching.
    """
    common = config.get("common", {})
    stage = config.get("stage", {})
    states = config.get("states", {})
    state = states.get(state_name, {})

    if not isinstance(common, dict):
        common = {}
    if not isinstance(stage, dict):
        stage = {}
    if not isinstance(states, dict):
        state = {}
    if not isinstance(state, dict):
        state = {}

    if interaction_type not in {"evaluation", "coaching"}:
        raise ValueError(f"Unknown interaction_type: {interaction_type}")

    parts = [
        _get_text(common, "preamble"),
        _get_text(common, "role"),
        _get_text(common, "rules"),
        _get_text(common, "output_spec"),
        _get_text(stage, "purpose"),
        _get_text(stage, "rules"),
        _get_text(stage, interaction_type),
        _get_text(state, "purpose"),
        _get_text(state, interaction_type),
    ]

    return "\n\n".join(part for part in parts if part)


# ============================================================================
# Runtime Payload Appending
# ============================================================================

def _format_history(history: list[Any] | None) -> str:
    """
    Format runtime chat history for prompt appending.

    History is deliberately appended after YAML assembly so it cannot alter the
    fixed prompt-fragment order from the stage template.
    """
    if not history:
        return ""

    lines = []
    for item in history:
        role = getattr(item, "role", None)
        message = getattr(item, "message", None)

        if role is not None and message is not None:
            role_value = getattr(role, "value", role)
            lines.append(f"{role_value}: {message}")
            continue

        if isinstance(item, dict):
            lines.append(f"{item.get('role', 'unknown')}: {item.get('message', item)}")
            continue

        lines.append(str(item))

    return "\n".join(lines)


def _append_runtime_context(
    prompt: str,
    user_message: str | None,
    history: list[Any] | None = None,
    context: dict[str, Any] | None = None,
    output_instruction: str | None = None,
) -> str:
    """
    Append runtime payload after the fixed YAML prompt text.

    Runtime payload includes user/session-specific data such as conversation
    history, context, latest user message, and optional output instructions.
    These are not part of the YAML text asset.
    """
    runtime_parts = []

    formatted_history = _format_history(history)
    if formatted_history:
        runtime_parts.append(f"Conversation history:\n{formatted_history}")

    if context:
        runtime_parts.append(
            "Context payload:\n"
            f"{json.dumps(context, indent=2, sort_keys=True, default=str)}"
        )

    if user_message:
        runtime_parts.append(f"Latest user message:\n{user_message}")

    if output_instruction:
        runtime_parts.append(f"Output instruction:\n{output_instruction}")

    if not runtime_parts:
        return prompt

    return "\n\n".join(
        [
            prompt,
            "Runtime payload:",
            "\n\n".join(runtime_parts),
        ]
    )


# ============================================================================
# LLM Boundary And Output Extraction
# ============================================================================

def _call_llm(prompt: str) -> tuple[str | None, str]:
    """
    Optionally call the LLM.

    The current repo had no live LLM plumbing, so calls are opt-in to keep smoke
    tests and local development offline-safe.
    """
    llm_enabled = os.getenv("COACHV3_USE_LLM", "").lower() in LLM_ENABLED_VALUES
    model = os.getenv("COACHV3_OPENAI_MODEL") or os.getenv("OPENAI_MODEL")

    if not llm_enabled:
        return None, "llm_call_status=disabled"

    if not model:
        return None, "llm_call_status=skipped_missing_model"

    if not os.getenv("OPENAI_API_KEY"):
        return None, "llm_call_status=skipped_missing_api_key"

    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(model=model, input=prompt)
        output_text = getattr(response, "output_text", None)

        if output_text:
            return str(output_text), "llm_call_status=ok"

        return str(response), "llm_call_status=ok_no_output_text"
    except Exception as exc:
        return None, f"llm_call_status=error llm_error={exc!r}"


def _extract_output(raw_output: str, structured: bool) -> dict[str, Any] | str:
    """
    Extract structured JSON output, or return plain text when requested.

    This intentionally stays simple: parse direct JSON first, then try the
    outermost JSON object if the model wrapped it in surrounding prose.
    """
    if not structured:
        return raw_output

    text = raw_output.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {
                "coach_message": text,
                "debug_message": "structured_parse_status=failed_no_json_object",
            }
        parsed = json.loads(text[start : end + 1])

    if isinstance(parsed, dict):
        return parsed

    return {
        "coach_message": str(parsed),
        "debug_message": "structured_parse_status=failed_json_not_object",
    }


# ============================================================================
# Debug Helpers
# ============================================================================

def _with_debug(
    output: dict[str, Any],
    debug_lines: list[str],
) -> dict[str, Any]:
    """Append engine debug lines without dropping model/fallback debug output."""
    existing_debug = str(output.get("debug_message") or "").strip()
    merged_debug = [existing_debug, *debug_lines] if existing_debug else debug_lines
    output["debug_message"] = "\n".join(line for line in merged_debug if line)
    return output


def _prompt_preview(prompt: str) -> str:
    """Return a compact prompt preview for debug traces."""
    preview = " ".join(prompt.split())
    if len(preview) <= 240:
        return preview
    return f"{preview[:240]}..."


def _raw_llm_reply_debug(interaction_type: str, raw_output: str | None) -> str:
    """Return the full raw LLM reply with clear debug boundaries."""
    if raw_output is None:
        return f"{interaction_type}_llm_reply_raw=<none>"

    return "\n".join(
        [
            f"{interaction_type}_llm_reply_raw_begin",
            raw_output,
            f"{interaction_type}_llm_reply_raw_end",
        ]
    )


def _full_prompt_debug(interaction_type: str, prompt: str) -> str:
    """Return the full prompt with clear debug boundaries."""
    return "\n".join(
        [
            f"{interaction_type}_prompt_full_begin",
            prompt,
            f"{interaction_type}_prompt_full_end",
        ]
    )


# ============================================================================
# Public API Helpers
# ============================================================================

def _run_interaction(
    interaction_type: str,
    stage_yaml_path: str | Path,
    state_name: str,
    user_message: str | None,
    history: list[Any] | None = None,
    context: dict[str, Any] | None = None,
    output_instruction: str | None = None,
    structured: bool = True,
    no_output_structured: dict[str, Any] | None = None,
    no_output_plain: str | None = None,
) -> dict[str, Any] | str:
    """Run one engine interaction while keeping evaluate/coach wrappers thin."""
    config_path = Path(stage_yaml_path)
    config = _load_stage_config(config_path)
    yaml_prompt = _assemble_prompt(config, state_name, interaction_type)
    prompt = _append_runtime_context(
        prompt=yaml_prompt,
        user_message=user_message,
        history=history,
        context=context,
        output_instruction=output_instruction,
    )

    raw_output, llm_debug = _call_llm(prompt)

    if raw_output:
        output = _extract_output(raw_output, structured=structured)
    elif not structured and no_output_plain is not None:
        return no_output_plain
    else:
        output = no_output_structured or {
            "debug_message": "structured_parse_status=no_llm_output",
        }

    if not isinstance(output, dict):
        return output

    return _with_debug(
        output,
        [
            f"config_status=loaded config_path={config_path}",
            llm_debug,
            _raw_llm_reply_debug(interaction_type, raw_output),
            f"stage_state={state_name}",
            f"interaction_type={interaction_type}",
            _full_prompt_debug(interaction_type, prompt),
            f"prompt_preview={_prompt_preview(prompt)}",
        ],
    )


# ============================================================================
# Public APIs
# ============================================================================

def evaluate(
    stage_yaml_path: str | Path,
    state_name: str,
    user_message: str | None,
    history: list[Any] | None = None,
    context: dict[str, Any] | None = None,
    output_instruction: str | None = None,
    structured: bool = True,
) -> dict[str, Any] | str:
    """
    Build an evaluation prompt, call the LLM if enabled, and extract output.

    Caller contract:
    - pass the stage YAML path explicitly
    - pass the current local state name explicitly
    - pass runtime payload separately from YAML text
    - request structured output with structured=True when the stage module needs
      fields such as evaluation_message or other stage-specific evaluation data

    The returned object is a dict when structured=True and extraction succeeds.
    The engine does not decide what state transition should happen next.
    """
    return _run_interaction(
        interaction_type="evaluation",
        stage_yaml_path=stage_yaml_path,
        state_name=state_name,
        user_message=user_message,
        history=history,
        context=context,
        output_instruction=output_instruction,
        structured=structured,
        no_output_structured={
            "evaluation_message": "TODO: engine evaluation not implemented yet.",
            "debug_message": "structured_parse_status=no_llm_output",
        },
    )


def coach(
    stage_yaml_path: str | Path,
    state_name: str,
    user_message: str | None,
    history: list[Any] | None = None,
    context: dict[str, Any] | None = None,
    output_instruction: str | None = None,
    structured: bool = False,
) -> dict[str, Any] | str:
    """
    Build a coaching prompt, call the LLM if enabled, and extract output.

    This mirrors evaluate(...), but uses the coaching prompt-fragment order and
    defaults to plain text output because coaching replies are usually
    user-facing messages.
    """
    return _run_interaction(
        interaction_type="coaching",
        stage_yaml_path=stage_yaml_path,
        state_name=state_name,
        user_message=user_message,
        history=history,
        context=context,
        output_instruction=output_instruction,
        structured=structured,
        no_output_structured={
            "coach_message": "TODO: engine coach message not implemented yet.",
            "debug_message": "structured_parse_status=no_llm_output",
        },
        no_output_plain="TODO: engine coach message not implemented yet.",
    )
