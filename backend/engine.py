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
import re
from pathlib import Path
from typing import Any

import yaml


LLM_ENABLED_VALUES = {"1", "true", "yes", "on"}


# ============================================================================
# YAML Loading And Text Assembly
# ============================================================================

def _load_stage_config(path: str | Path) -> dict[str, Any]:
    """
    Load one stage YAML file and return the raw mapping.

    The engine expects each stage file to follow the V3 template shape:
    - experience
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
    1. experience.prompt_preamble
    2. experience.role
    3. experience.global_rules
    4. experience.shared_output_rules
    5. experience.evaluation
    6. stage.prompt_preamble
    7. stage.purpose
    8. stage.rules
    9. stage.shared_output_rules
    10. stage.evaluation
    11. states.<state>.prompt_preamble
    12. states.<state>.purpose
    13. states.<state>.rules
    14. states.<state>.shared_output_rules
    15. states.<state>.evaluation

    Coaching uses the same order, replacing evaluation with coaching.
    """
    experience = config.get("experience", {})
    stage = config.get("stage", {})
    states = config.get("states", {})
    state = states.get(state_name, {})

    if not isinstance(experience, dict):
        experience = {}
    if not isinstance(stage, dict):
        stage = {}
    if not isinstance(states, dict):
        state = {}
    if not isinstance(state, dict):
        state = {}

    if interaction_type not in {"evaluation", "coaching"}:
        raise ValueError(f"Unknown interaction_type: {interaction_type}")

    parts = [
        _get_text(experience, "prompt_preamble"),
        _get_text(experience, "role"),
        _get_text(experience, "global_rules"),
        _get_text(experience, "shared_output_rules"),
        _get_text(experience, interaction_type),
        _get_text(stage, "prompt_preamble"),
        _get_text(stage, "purpose"),
        _get_text(stage, "rules"),
        _get_text(stage, "shared_output_rules"),
        _get_text(stage, interaction_type),
        _get_text(state, "prompt_preamble"),
        _get_text(state, "purpose"),
        _get_text(state, "rules"),
        _get_text(state, "shared_output_rules"),
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
# Temporary Offline Fallback
# ============================================================================

def _classification_fallback_output(user_message: str | None) -> dict[str, str]:
    """
    Offline deterministic fallback for the existing Classification smoke path.

    This preserves local tests until live LLM calls are enabled. It is not a
    replacement for the new YAML prompt assembly and should stay outside stage
    FSM decisions.
    """
    normalized = " ".join((user_message or "").strip().lower().split())
    tokens = re.findall(r"[a-z']+", normalized)

    coaching_keywords = [
        "work",
        "career",
        "manager",
        "team",
        "relationship",
        "conflict",
        "stress",
        "overwhelmed",
        "burnout",
        "decision",
        "decide",
        "goal",
        "priorities",
        "communication",
        "boundaries",
    ]
    ambiguous_keywords = [
        "help",
        "advice",
        "stuck",
        "unsure",
        "not sure",
        "something",
        "issue",
        "problem",
    ]
    invalid_keywords = [
        "weather",
        "joke",
        "recipe",
        "sports score",
        "stock price",
        "movie review",
        "trivia",
    ]

    matched_invalid_keyword = next(
        (keyword for keyword in invalid_keywords if keyword in normalized),
        None,
    )
    matched_ambiguous_keyword = next(
        (keyword for keyword in ambiguous_keywords if keyword in normalized),
        None,
    )
    matched_coaching_keyword = next(
        (keyword for keyword in coaching_keywords if keyword in normalized),
        None,
    )

    if matched_invalid_keyword:
        label = "invalid"
        reason = f"matched invalid topic keyword '{matched_invalid_keyword}'"
    elif len(tokens) < 6:
        label = "ambiguous"
        reason = (
            f"message only contains {len(tokens)} word(s), which is below "
            "the valid threshold of 6"
        )
    elif matched_coaching_keyword:
        label = "valid"
        reason = (
            f"matched coaching keyword '{matched_coaching_keyword}' "
            "with enough detail"
        )
    elif matched_ambiguous_keyword and len(tokens) < 9:
        label = "ambiguous"
        reason = (
            f"matched ambiguity keyword '{matched_ambiguous_keyword}' "
            "and still lacks context"
        )
    else:
        label = "ambiguous"
        reason = "message does not yet clearly describe a coaching issue"

    messages = {
        "valid": {
            "evaluation": (
                "Classification result: valid. The opening message contains "
                "a coaching-suitable issue with enough context to proceed."
            ),
            "coach": (
                "Thanks. That sounds like a real situation we can work "
                "through, so let's begin."
            ),
        },
        "ambiguous": {
            "evaluation": (
                "Classification result: ambiguous. The opening message may "
                "be coaching-relevant, but it still needs clarification."
            ),
            "coach": (
                "I can help, but I need one clearer sentence about the "
                "decision, challenge, or conflict you want coaching on."
            ),
        },
        "invalid": {
            "evaluation": (
                "Classification result: invalid. The opening message does "
                "not fit the coaching intake flow."
            ),
            "coach": (
                "I can't continue this session because the opening message "
                "does not describe a coaching issue I can work on here."
            ),
        },
    }

    return {
        "classification_label": label,
        "evaluation_message": f"{messages[label]['evaluation']} Reason: {reason}.",
        "coach_message": messages[label]["coach"],
        "debug_message": "\n".join(
            [
                "classification_engine=offline_fallback_v1",
                "parse_status=offline_fallback",
                f"classification_outcome={label}",
                f"classification_reason={reason}",
                f"matched_invalid_keyword={matched_invalid_keyword or 'none'}",
                f"matched_ambiguous_keyword={matched_ambiguous_keyword or 'none'}",
                f"matched_coaching_keyword={matched_coaching_keyword or 'none'}",
            ]
        ),
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
      fields such as evaluation_message, coach_message, or classification_label

    The returned object is a dict when structured=True and extraction succeeds.
    The engine does not decide what state transition should happen next.
    """
    config_path = Path(stage_yaml_path)
    config = _load_stage_config(config_path)
    yaml_prompt = _assemble_prompt(config, state_name, "evaluation")
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
    elif config_path.stem == "classification" and structured:
        output = _classification_fallback_output(user_message)
    else:
        output = {
            "evaluation_message": "TODO: engine evaluation not implemented yet.",
            "coach_message": None,
            "debug_message": "structured_parse_status=no_llm_output",
        }

    if not isinstance(output, dict):
        return output

    return _with_debug(
        output,
        [
            f"config_status=loaded config_path={config_path}",
            llm_debug,
            f"stage_state={state_name}",
            f"interaction_type=evaluation",
            f"prompt_preview={_prompt_preview(prompt)}",
        ],
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
    config_path = Path(stage_yaml_path)
    config = _load_stage_config(config_path)
    yaml_prompt = _assemble_prompt(config, state_name, "coaching")
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
    elif structured:
        output = {
            "coach_message": "TODO: engine coach message not implemented yet.",
            "debug_message": "structured_parse_status=no_llm_output",
        }
    else:
        return "TODO: engine coach message not implemented yet."

    if not isinstance(output, dict):
        return output

    return _with_debug(
        output,
        [
            f"config_status=loaded config_path={config_path}",
            llm_debug,
            f"stage_state={state_name}",
            f"interaction_type=coaching",
            f"prompt_preview={_prompt_preview(prompt)}",
        ],
    )
