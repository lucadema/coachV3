"""Backend-only telemetry assessment helpers.

These assessments are deliberately best-effort. They classify existing session
content into controlled telemetry values and must never affect the active
coaching flow.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

import yaml

from backend import engine
from backend.enums import ChatRole
from backend.models import Session


logger = logging.getLogger(__name__)

PROMPT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "telemetry_assessment_prompts.yaml"
)

PROBLEM_CATEGORY_VALUES = {
    "organisational_friction",
    "lack_of_clarity_alignment",
    "poor_decision_making",
    "siloed_thinking",
    "strategy_execution_gap",
    "inability_to_adapt",
}

ENGAGEMENT_SIGNAL_VALUES = {
    "no_visible_risk",
    "frustration_signal",
    "voice_suppression_signal",
    "disengagement_risk",
}

RawLlmCaller = Callable[[str, str, str | None], str | None]


def assess_synthesis_telemetry(
    session: Session,
    *,
    synthesis_text: str | None,
    config_path: str | Path = PROMPT_CONFIG_PATH,
    raw_llm_caller: RawLlmCaller | None = None,
) -> None:
    """Populate null telemetry assessment fields from the just-generated synthesis."""
    if not str(synthesis_text or "").strip():
        return None

    prompts = _load_prompts(config_path)
    caller = raw_llm_caller or _call_raw_llm

    if session.problem_category is None:
        session.problem_category = _assess_single_field(
            prompt=prompts.get("problem_category_prompt"),
            field_name="problem_category",
            allowed_values=PROBLEM_CATEGORY_VALUES,
            source_label="Synthesis",
            source_text=str(synthesis_text or ""),
            llm_operation="telemetry.problem_category",
            session_id=session.session_id,
            raw_llm_caller=caller,
        )

    if session.engagement_signal is None:
        transcript = _conversation_transcript_before_synthesis(session)
        session.engagement_signal = _assess_single_field(
            prompt=prompts.get("engagement_signal_prompt"),
            field_name="engagement_signal",
            allowed_values=ENGAGEMENT_SIGNAL_VALUES,
            source_label="Conversation transcript before synthesis",
            source_text=transcript,
            llm_operation="telemetry.engagement_signal",
            session_id=session.session_id,
            raw_llm_caller=caller,
        )

    return None


def parse_controlled_json_value(
    raw_output: str | None,
    *,
    field_name: str,
    allowed_values: set[str],
) -> str | None:
    """Parse strict JSON and return one allowed controlled value, otherwise null."""
    text = str(raw_output or "").strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict) or set(parsed.keys()) != {field_name}:
        return None

    value = parsed.get(field_name)
    if value is None:
        return None

    if isinstance(value, str) and value in allowed_values:
        return value

    return None


def _load_prompts(config_path: str | Path) -> dict[str, str]:
    path = Path(config_path)
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
    except Exception as exc:
        logger.warning(
            "Telemetry assessment prompt config failed path=%s error_type=%s error=%s",
            path,
            type(exc).__name__,
            str(exc)[:300],
        )
        return {}

    if not isinstance(loaded, dict):
        logger.warning("Telemetry assessment prompt config root is not a mapping path=%s", path)
        return {}

    prompts: dict[str, str] = {}
    for key in ("problem_category_prompt", "engagement_signal_prompt"):
        value = loaded.get(key)
        if isinstance(value, str) and value.strip():
            prompts[key] = value.strip()

    return prompts


def _assess_single_field(
    *,
    prompt: str | None,
    field_name: str,
    allowed_values: set[str],
    source_label: str,
    source_text: str | None,
    llm_operation: str,
    session_id: str,
    raw_llm_caller: RawLlmCaller,
) -> str | None:
    source = str(source_text or "").strip()
    if not prompt or not source:
        return None

    full_prompt = f"{prompt}\n\n{source_label}:\n{source}"

    try:
        raw_output = raw_llm_caller(full_prompt, llm_operation, session_id)
    except Exception as exc:
        logger.warning(
            "Telemetry assessment LLM failed field=%s error_type=%s error=%s",
            field_name,
            type(exc).__name__,
            str(exc)[:300],
        )
        return None

    return parse_controlled_json_value(
        raw_output,
        field_name=field_name,
        allowed_values=allowed_values,
    )


def _conversation_transcript_before_synthesis(session: Session) -> str:
    lines: list[str] = []
    for item in session.chat_history:
        message = item.message.strip()
        if not message:
            continue

        if item.role == ChatRole.USER:
            role = "User"
        elif item.role == ChatRole.ASSISTANT:
            role = "Coach"
        else:
            role = str(item.role.value if hasattr(item.role, "value") else item.role)

        lines.append(f"{role}: {message}")

    return "\n".join(lines).strip()


def _call_raw_llm(prompt: str, llm_operation: str, session_id: str | None) -> str | None:
    raw_output, debug = engine.run_raw_prompt(
        prompt=prompt,
        llm_operation=llm_operation,
        telemetry_session_id=session_id,
    )
    if raw_output is None and "llm_call_status=error" in debug:
        logger.warning("Telemetry assessment LLM returned error debug=%s", debug[:300])

    return raw_output
