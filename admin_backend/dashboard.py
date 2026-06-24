"""Aggregate, anonymised pilot dashboard helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from backend.feedback import FeedbackConfig, FeedbackConfigError, load_feedback_config


PROBLEM_CATEGORY_LABELS: dict[str, str] = {
    "organisational_friction": "Organisational friction",
    "lack_of_clarity_alignment": "Lack of clarity and alignment",
    "poor_decision_making": "Poor decision-making",
    "siloed_thinking": "Siloed thinking",
    "strategy_execution_gap": "Strategy/execution gap",
    "inability_to_adapt": "Inability to adapt",
}

ENGAGEMENT_SIGNAL_LABELS: dict[str, str] = {
    "no_visible_risk": "No visible risk",
    "frustration_signal": "Frustration signal",
    "voice_suppression_signal": "Voice suppression signal",
    "disengagement_risk": "Disengagement risk",
}

VALUE_TIME_QUESTION_ID = "weekly_time_saved"
VALUE_PEOPLE_QUESTION_ID = "people_who_would_benefit"
FLAG_TO_ORGANISATION_QUESTION_ID = "flag_to_organisation"
WEEKS_PER_MONTH = 4
VALUE_QUESTION_IDS = (VALUE_TIME_QUESTION_ID, VALUE_PEOPLE_QUESTION_ID)

# TODO: Wire in a configurable anonymity threshold if the product defines one.
DASHBOARD_ANONYMITY_THRESHOLD: int | None = None

ValueOptionMappings = dict[str, dict[str, dict[str, float]]]


def build_count_buckets(
    raw_counts: Mapping[str, Any] | None,
    labels_by_value: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Return stable dashboard count buckets for recognised controlled values."""
    counts = raw_counts or {}
    buckets: list[dict[str, Any]] = []
    for value, label in labels_by_value.items():
        buckets.append(
            {
                "value": value,
                "label": label,
                "count": _nonnegative_int(counts.get(value)),
            }
        )
    return buckets


def load_value_option_mappings() -> ValueOptionMappings:
    """Return configured numeric option mappings for value dashboard inputs."""
    try:
        config = load_feedback_config()
    except FeedbackConfigError:
        return {}
    return build_value_option_mappings(config)


def build_value_option_mappings(config: FeedbackConfig) -> ValueOptionMappings:
    mappings: ValueOptionMappings = {}

    for pack_id, pack in config.feedback_packs.items():
        pack_mappings: dict[str, dict[str, float]] = {}
        for question in pack.questions:
            if question.id not in VALUE_QUESTION_IDS:
                continue

            option_mappings = {
                option.value: float(option.numeric_value)
                for option in question.options
                if _positive_number(option.numeric_value) is not None
            }
            if option_mappings:
                pack_mappings[question.id] = option_mappings

        if pack_mappings:
            mappings[pack_id] = pack_mappings

    return mappings


def calculate_value_inputs(
    feedback_responses: Iterable[Any],
    option_mappings: ValueOptionMappings | None = None,
) -> dict[str, Any]:
    """Calculate monthly-minute inputs from complete value feedback responses.

    The current implemented pilot impact pack stores weekly minutes and people
    affected as normalised single-select responses with server-side
    ``numeric_value`` fields. Rows without both values are excluded.
    """
    monthly_minutes = 0.0
    qualifying_responses_count = 0
    flag_yes_count = 0
    flag_no_count = 0

    mappings = option_mappings if option_mappings is not None else load_value_option_mappings()

    for item in feedback_responses:
        pack_id, responses = _feedback_row_parts(item)
        if responses is None:
            continue

        flag_answer = responses.get(FLAG_TO_ORGANISATION_QUESTION_ID)
        if flag_answer is True:
            flag_yes_count += 1
        elif flag_answer is False:
            flag_no_count += 1

        weekly_minutes = _numeric_answer(
            responses,
            VALUE_TIME_QUESTION_ID,
            pack_id=pack_id,
            option_mappings=mappings,
        )
        people = _numeric_answer(
            responses,
            VALUE_PEOPLE_QUESTION_ID,
            pack_id=pack_id,
            option_mappings=mappings,
        )
        if weekly_minutes is None or people is None:
            continue

        monthly_minutes += people * weekly_minutes * WEEKS_PER_MONTH
        qualifying_responses_count += 1

    return {
        "monthly_minutes": monthly_minutes,
        "qualifying_responses_count": qualifying_responses_count,
        "flag_to_organisation": {
            "yes_count": flag_yes_count,
            "no_count": flag_no_count,
        },
    }


def _feedback_row_parts(value: Any) -> tuple[str | None, Mapping[str, Any] | None]:
    if isinstance(value, Mapping) and "feedback_responses" in value:
        pack_id = value.get("feedback_pack_id")
        return (
            pack_id.strip() if isinstance(pack_id, str) and pack_id.strip() else None,
            _response_mapping(value.get("feedback_responses")),
        )

    return None, _response_mapping(value)


def _response_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, Mapping):
            return parsed

    return None


def _numeric_answer(
    responses: Mapping[str, Any],
    question_id: str,
    *,
    pack_id: str | None,
    option_mappings: ValueOptionMappings,
) -> float | None:
    raw_answer = responses.get(question_id)
    if isinstance(raw_answer, Mapping):
        return _positive_number(raw_answer.get("numeric_value"))

    if isinstance(raw_answer, str):
        return _mapped_option_number(
            raw_answer,
            question_id,
            pack_id=pack_id,
            option_mappings=option_mappings,
        )

    return None


def _mapped_option_number(
    option_value: str,
    question_id: str,
    *,
    pack_id: str | None,
    option_mappings: ValueOptionMappings,
) -> float | None:
    if pack_id:
        return option_mappings.get(pack_id, {}).get(question_id, {}).get(option_value)

    matches = [
        question_mapping[option_value]
        for pack_mapping in option_mappings.values()
        for mapped_question_id, question_mapping in pack_mapping.items()
        if mapped_question_id == question_id and option_value in question_mapping
    ]
    if len(matches) == 1:
        return matches[0]

    return None


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int | float) and value > 0:
        return float(value)

    return None


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0

    if isinstance(value, int) and value >= 0:
        return value

    return 0
