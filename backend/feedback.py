"""Configurable feedback form loading, validation, and storage."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend import pilot_access
from backend import telemetry
from backend.models import Session
from backend.state_store import state_store


logger = logging.getLogger(__name__)

DEFAULT_FEEDBACK_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "feedback_forms.yaml"
SUPPORTED_QUESTION_TYPES = {
    "boolean",
    "likert_1_5",
    "single_select",
    "multi_select",
    "short_text",
    "free_text",
}


class FeedbackConfigError(RuntimeError):
    """Raised when feedback configuration cannot be used."""


class FeedbackValidationError(ValueError):
    """Raised when a feedback submission does not match its configured pack."""


class FeedbackOption(BaseModel):
    value: str
    label: str
    numeric_value: int | float | None = None


class FeedbackQuestion(BaseModel):
    id: str
    type: Literal[
        "boolean",
        "likert_1_5",
        "single_select",
        "multi_select",
        "short_text",
        "free_text",
    ]
    text: str
    required: bool = False
    placeholder: str | None = None
    true_label: str | None = None
    false_label: str | None = None
    options: list[FeedbackOption] = Field(default_factory=list)

    @field_validator("options")
    @classmethod
    def validate_option_values(cls, options: list[FeedbackOption]) -> list[FeedbackOption]:
        values = [option.value for option in options]
        if len(values) != len(set(values)):
            raise ValueError("option values must be unique per question")
        return options


class FeedbackPack(BaseModel):
    label: str
    title: str
    survey_query: str
    description: str | None = None
    questions: list[FeedbackQuestion]

    @field_validator("questions")
    @classmethod
    def validate_question_ids(cls, questions: list[FeedbackQuestion]) -> list[FeedbackQuestion]:
        ids = [question.id for question in questions]
        if len(ids) != len(set(ids)):
            raise ValueError("question ids must be unique per feedback pack")
        return questions


class FeedbackConfig(BaseModel):
    default_feedback_pack_id: str | None = None
    feedback_packs: dict[str, FeedbackPack] = Field(default_factory=dict)


class FeedbackFormResponse(BaseModel):
    show_feedback: bool
    feedback_pack_id: str | None = None
    title: str | None = None
    survey_query: str | None = None
    description: str | None = None
    questions: list[FeedbackQuestion] = Field(default_factory=list)


class FeedbackSubmission(BaseModel):
    session_id: str
    feedback_pack_id: str
    responses: dict[str, Any] = Field(default_factory=dict)


def load_feedback_config(
    config_path: Path = DEFAULT_FEEDBACK_CONFIG_PATH,
) -> FeedbackConfig:
    """Load and validate the feedback YAML config."""
    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FeedbackConfigError("feedback_config_missing") from exc
    except yaml.YAMLError as exc:
        raise FeedbackConfigError("feedback_config_invalid_yaml") from exc

    if not isinstance(raw_config, dict):
        raise FeedbackConfigError("feedback_config_invalid_shape")

    try:
        config = FeedbackConfig.model_validate(raw_config)
    except ValidationError as exc:
        raise FeedbackConfigError("feedback_config_invalid_schema") from exc

    default_pack_id = config.default_feedback_pack_id
    if not default_pack_id or default_pack_id not in config.feedback_packs:
        raise FeedbackConfigError("feedback_config_default_pack_missing")

    for pack in config.feedback_packs.values():
        for question in pack.questions:
            if question.type in {"single_select", "multi_select"} and not question.options:
                raise FeedbackConfigError("feedback_config_select_question_without_options")
            if question.type not in {"single_select", "multi_select"} and question.options:
                raise FeedbackConfigError("feedback_config_options_on_non_select_question")

    return config


def get_default_feedback_pack() -> tuple[str, FeedbackPack] | None:
    """Return the default pack, logging and failing closed when config is bad."""
    try:
        config = load_feedback_config()
    except FeedbackConfigError as exc:
        logger.warning("Feedback form unavailable: %s", exc)
        return None

    pack_id = config.default_feedback_pack_id
    if not pack_id:
        return None
    return pack_id, config.feedback_packs[pack_id]


def get_feedback_pack(pack_id: str) -> FeedbackPack:
    config = load_feedback_config()
    try:
        return config.feedback_packs[pack_id]
    except KeyError as exc:
        raise FeedbackValidationError("unknown_feedback_pack_id") from exc


def get_active_feedback_form(session: Session) -> FeedbackFormResponse:
    try:
        config = load_feedback_config()
    except FeedbackConfigError as exc:
        logger.warning("Feedback form unavailable: %s", exc)
        return FeedbackFormResponse(show_feedback=False)

    pack_id = _select_feedback_pack_id(session, config)
    pack = config.feedback_packs[pack_id]
    return FeedbackFormResponse(
        show_feedback=True,
        feedback_pack_id=pack_id,
        title=pack.title,
        survey_query=pack.survey_query,
        description=pack.description,
        questions=pack.questions,
    )


def _select_feedback_pack_id(session: Session, config: FeedbackConfig) -> str:
    default_pack_id = config.default_feedback_pack_id
    if not default_pack_id:
        raise FeedbackConfigError("feedback_config_default_pack_missing")

    pilot_id = (session.pilot_id or "").strip()
    if not pilot_id:
        return default_pack_id

    try:
        pilot_pack_id = pilot_access.get_pilot_feedback_pack_id(pilot_id)
    except Exception as exc:
        logger.warning(
            "Falling back to default feedback pack after pilot lookup error "
            "pilot_id=%s error_type=%s error=%s",
            pilot_id,
            type(exc).__name__,
            str(exc)[:300],
        )
        return default_pack_id

    if not pilot_pack_id:
        return default_pack_id

    if pilot_pack_id not in config.feedback_packs:
        logger.warning(
            "Falling back to default feedback pack because pilot pack is unknown "
            "pilot_id=%s feedback_pack_id=%s",
            pilot_id,
            pilot_pack_id,
        )
        return default_pack_id

    return pilot_pack_id


def normalise_feedback_responses(
    pack: FeedbackPack,
    responses: dict[str, Any],
) -> dict[str, Any]:
    questions_by_id = {question.id: question for question in pack.questions}
    normalised: dict[str, Any] = {}

    unknown_question_ids = sorted(set(responses) - set(questions_by_id))
    if unknown_question_ids:
        raise FeedbackValidationError(f"unknown_feedback_question_id:{unknown_question_ids[0]}")

    for question in pack.questions:
        has_value = question.id in responses
        value = responses.get(question.id)

        if not has_value or value is None or value == "" or value == []:
            if question.required:
                raise FeedbackValidationError(f"required_feedback_question_missing:{question.id}")
            continue

        normalised[question.id] = _normalise_question_response(question, value)

    return normalised


def store_feedback_submission(submission: FeedbackSubmission) -> Session:
    """Validate and persist feedback in the canonical session and telemetry sink."""
    session = state_store.get_session(submission.session_id)
    if session is None:
        raise FeedbackValidationError("session_not_found")

    pack = get_feedback_pack(submission.feedback_pack_id)
    normalised_responses = normalise_feedback_responses(pack, submission.responses)

    session.feedback_pack_id = submission.feedback_pack_id
    session.feedback_responses = normalised_responses
    state_store.save_session(session)

    telemetry.record_feedback_submitted(
        session_id=session.session_id,
        feedback_pack_id=submission.feedback_pack_id,
        feedback_responses=normalised_responses,
        pilot_id=session.pilot_id,
    )
    state_store.delete_session(session.session_id)

    return session


def _normalise_question_response(question: FeedbackQuestion, value: Any) -> Any:
    if question.type == "boolean":
        if not isinstance(value, bool):
            raise FeedbackValidationError(f"invalid_boolean_feedback:{question.id}")
        return value

    if question.type == "likert_1_5":
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 5:
            raise FeedbackValidationError(f"invalid_likert_feedback:{question.id}")
        return value

    if question.type == "single_select":
        if not isinstance(value, str):
            raise FeedbackValidationError(f"invalid_single_select_feedback:{question.id}")
        option = _option_by_value(question, value)
        if option is None:
            raise FeedbackValidationError(f"invalid_single_select_option:{question.id}")
        if option.numeric_value is None:
            return {"value": option.value}
        return {"value": option.value, "numeric_value": option.numeric_value}

    if question.type == "multi_select":
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise FeedbackValidationError(f"invalid_multi_select_feedback:{question.id}")
        option_values = {option.value for option in question.options}
        for selected_value in value:
            if selected_value not in option_values:
                raise FeedbackValidationError(f"invalid_multi_select_option:{question.id}")
        return value

    if question.type in {"short_text", "free_text"}:
        if not isinstance(value, str):
            raise FeedbackValidationError(f"invalid_text_feedback:{question.id}")
        return value

    raise FeedbackValidationError(f"unsupported_feedback_question_type:{question.id}")


def _option_by_value(question: FeedbackQuestion, value: str) -> FeedbackOption | None:
    for option in question.options:
        if option.value == value:
            return option
    return None
