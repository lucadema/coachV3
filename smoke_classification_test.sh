#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  python_bin="$PYTHON_BIN"
elif [[ -x "venv/bin/python" ]]; then
  python_bin="venv/bin/python"
else
  python_bin="python"
fi

export COACHV3_USE_LLM=0

"$python_bin" -m py_compile \
  backend/engine.py \
  backend/controller.py \
  backend/models.py \
  backend/stages/classification.py \
  smoke_test.py

"$python_bin" - <<'PY'
from pathlib import Path

import yaml

from backend import engine
from backend.controller import handle_user_msg, init_session
from backend.enums import ClassificationState, CoachingState, Stage, StateType
from backend.models import Session
from backend.state_store import state_store
from backend.stages import classification


CONFIG_PATH = Path("backend/config/classification.yaml")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK: {message}")


print("== Classification YAML shape ==")
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
check(isinstance(config, dict), "classification.yaml root is a mapping")
for section_name in ("meta", "common", "stage", "states"):
    check(isinstance(config.get(section_name), dict), f"classification.yaml has {section_name} mapping")
check(config["meta"].get("stage") == "classification", "meta.stage is classification")
check(
    classification.get_state_type(ClassificationState.EVALUATING.value) == StateType.EVALUATIVE.value,
    "Classification evaluating state is evaluative",
)
check(
    classification.get_state_type(ClassificationState.AMBIGUOUS.value) == StateType.WAITING.value,
    "Classification ambiguous state is waiting",
)


print("== Engine public API compatibility ==")
evaluation_result = engine.evaluate(
    stage_yaml_path=CONFIG_PATH,
    state_name=ClassificationState.EVALUATING.value,
    user_message="I need help deciding how to handle a conflict with my manager at work.",
    structured=True,
)
check(isinstance(evaluation_result, dict), "evaluate returns structured output")
check(
    evaluation_result.get("evaluation_message") == "TODO: engine evaluation not implemented yet.",
    "engine evaluate stays generic when no LLM output is available",
)
check(
    "interaction_type=evaluation" in str(evaluation_result.get("debug_message", "")),
    "evaluate uses evaluation prompt path",
)

coaching_result = engine.coach(
    stage_yaml_path=CONFIG_PATH,
    state_name=ClassificationState.AMBIGUOUS.value,
    user_message="I need help with work priorities.",
    structured=True,
)
check(isinstance(coaching_result, dict), "coach can return structured output")
check(
    "interaction_type=coaching" in str(coaching_result.get("debug_message", "")),
    "coach uses coaching prompt path",
)


print("== Local FSM normalization ==")
session = Session(
    session_id="classification-normalization",
    stage=Stage.CLASSIFICATION.value,
    state=ClassificationState.EVALUATING.value,
    user_message="Synthetic classification normalization check.",
)
reply = classification.apply_evaluation(
    session,
    {
        "classification_label": "AMBIGUOUS",
        "evaluation_message": "Classification result: ambiguous.",
        "debug_message": "fake_engine_label=AMBIGUOUS",
    },
)
check(
    reply.session.state == ClassificationState.AMBIGUOUS.value,
    "AMBIGUOUS label maps to ambiguous state",
)
check(reply.run_coaching is True, "AMBIGUOUS outcome requests coaching text")

session = Session(
    session_id="classification-out-of-scope",
    stage=Stage.CLASSIFICATION.value,
    state=ClassificationState.EVALUATING.value,
    user_message="Synthetic classification normalization check.",
)
reply = classification.apply_evaluation(
    session,
    {
        "classification_label": "OUT_OF_SCOPE",
        "evaluation_message": "Classification result: OUT_OF_SCOPE.",
        "debug_message": "fake_engine_label=OUT_OF_SCOPE",
    },
)
check(
    reply.session.state == ClassificationState.CANCELLED.value,
    "OUT_OF_SCOPE label maps to cancelled state",
)
check(reply.run_coaching is True, "OUT_OF_SCOPE outcome requests a boundary message")

print("== Stage-local offline fallback ==")
session = Session(
    session_id="classification-stage-fallback",
    stage=Stage.CLASSIFICATION.value,
    state=ClassificationState.EVALUATING.value,
    user_message="I need help deciding how to address a priorities conflict with my manager at work.",
)
reply = classification.apply_evaluation(
    session,
    {
        "evaluation_message": "TODO: engine evaluation not implemented yet.",
        "debug_message": "structured_parse_status=no_llm_output",
    },
)
check(
    reply.session.state == ClassificationState.COMPLETED.value,
    "classification stage applies its own offline fallback for valid intake",
)
check(
    "classification_fallback_source=stage_module" in str(reply.session.debug_message),
    "classification stage debug makes stage-local fallback explicit",
)


print("== Controller classification flows ==")
state_store.clear()

valid_session = init_session(session_id="classification-smoke-valid")
valid = handle_user_msg(
    valid_session.session_id,
    "I need help deciding how to address a priorities conflict with my manager at work.",
)
check(valid.stage == Stage.COACHING.value, "valid input advances into coaching")
check(valid.state == CoachingState.GUIDING.value, "valid input lands in coaching guiding")
check(valid.cancelled is False, "valid input does not cancel")

ambiguous_session = init_session(session_id="classification-smoke-ambiguous")
ambiguous = handle_user_msg(ambiguous_session.session_id, "I need help.")
check(ambiguous.stage == Stage.CLASSIFICATION.value, "ambiguous input stays in classification")
check(ambiguous.state == ClassificationState.AMBIGUOUS.value, "ambiguous input sets ambiguous state")
check(ambiguous.cancelled is False, "ambiguous input does not cancel immediately")

invalid_session = init_session(session_id="classification-smoke-invalid")
invalid = handle_user_msg(
    invalid_session.session_id,
    "Tell me the weather forecast for Rome tomorrow.",
)
check(invalid.stage == Stage.CLASSIFICATION.value, "invalid input stays in classification")
check(invalid.state == ClassificationState.CANCELLED.value, "invalid input cancels classification")
check(invalid.cancelled is True, "invalid input sets cancelled flag")

bounded_session = init_session(session_id="classification-smoke-bounded")
first_ambiguous = handle_user_msg(bounded_session.session_id, "I need help.")
first_ambiguous_state = first_ambiguous.state
second_ambiguous = handle_user_msg(
    bounded_session.session_id,
    "Still not sure, just help.",
)
check(first_ambiguous_state == ClassificationState.AMBIGUOUS.value, "bounded ambiguity first turn becomes ambiguous")
check(second_ambiguous.state == ClassificationState.CANCELLED.value, "bounded ambiguity cancels unresolved clarification")
check(second_ambiguous.cancelled is True, "bounded ambiguity sets cancelled flag")

print("Classification smoke checks passed.")
PY
