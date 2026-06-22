"""Aggregate, anonymised pilot dashboard helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any


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

# TODO: Wire in a configurable anonymity threshold if the product defines one.
DASHBOARD_ANONYMITY_THRESHOLD: int | None = None


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


def calculate_value_inputs(feedback_responses: Iterable[Any]) -> dict[str, Any]:
    """Calculate monthly-minute inputs from complete value feedback responses.

    The current implemented pilot impact pack stores weekly minutes and people
    affected as normalised single-select responses with server-side
    ``numeric_value`` fields. Rows without both values are excluded.
    """
    monthly_minutes = 0.0
    qualifying_responses_count = 0
    flag_yes_count = 0
    flag_no_count = 0

    for item in feedback_responses:
        responses = _response_mapping(item)
        if responses is None:
            continue

        flag_answer = responses.get(FLAG_TO_ORGANISATION_QUESTION_ID)
        if flag_answer is True:
            flag_yes_count += 1
        elif flag_answer is False:
            flag_no_count += 1

        weekly_minutes = _numeric_answer(responses, VALUE_TIME_QUESTION_ID)
        people = _numeric_answer(responses, VALUE_PEOPLE_QUESTION_ID)
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


def _numeric_answer(responses: Mapping[str, Any], question_id: str) -> float | None:
    raw_answer = responses.get(question_id)
    if not isinstance(raw_answer, Mapping):
        return None

    return _positive_number(raw_answer.get("numeric_value"))


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
