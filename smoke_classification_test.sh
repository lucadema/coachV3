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

"$python_bin" -m py_compile \
  backend/engine.py \
  backend/stages/classification.py \
  backend/controller.py \
  backend/models.py

"$python_bin" - <<'PY'
from pathlib import Path
import os

import yaml

from backend.controller import handle_user_msg, init_session
from backend.engine import coach, evaluate
from backend.enums import ClassificationState, CoachingState, Stage
from backend.models import Session
from backend.state_store import state_store
from backend.stages import classification


os.environ["COACHV3_USE_LLM"] = "0"
CONFIG_PATH = Path("backend/config/classification.yaml")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK: {message}")


print("== Classification YAML shape ==")
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
check(isinstance(config, dict), "classification.yaml root is a mapping")

for section_name in ("experience", "stage", "states"):
    check(
        isinstance(config.get(section_name), dict),
        f"classification.yaml has {section_name} mapping",
    )

for state_name in ("evaluating", "ambiguous", "completed", "cancelled"):
    state = config["states"].get(state_name)
    check(isinstance(state, dict), f"classification.yaml has {state_name} state")
    for key in (
        "prompt_preamble",
        "purpose",
        "rules",
        "shared_output_rules",
        "evaluation",
        "coaching",
    ):
        check(key in state, f"{state_name} state includes {key}")


print("== Engine public API compatibility ==")
evaluation_result = evaluate(
    stage_yaml_path=CONFIG_PATH,
    state_name=ClassificationState.EVALUATING.value,
    user_message=(
        "I need help deciding how to handle a conflict with my manager at work."
    ),
    structured=True,
)
check(isinstance(evaluation_result, dict), "evaluate returns structured output")
check(
    "config_status=loaded" in str(evaluation_result.get("debug_message", "")),
    "evaluate loads classification.yaml",
)
check(
    "interaction_type=evaluation" in str(evaluation_result.get("debug_message", "")),
    "evaluate uses evaluation prompt path",
)

coaching_result = coach(
    stage_yaml_path=CONFIG_PATH,
    state_name=ClassificationState.EVALUATING.value,
    user_message="I need help with work priorities.",
    structured=True,
)
check(isinstance(coaching_result, dict), "coach can return structured output")
check(
    "interaction_type=coaching" in str(coaching_result.get("debug_message", "")),
    "coach uses coaching prompt path",
)


print("== Controller classification flows ==")
state_store.clear()

valid_session = init_session(session_id="classification-smoke-valid")
valid = handle_user_msg(
    valid_session.session_id,
    "I need help deciding how to address a priorities conflict with my manager at work.",
)
check(valid.stage == Stage.COACHING.value, "valid input advances to coaching")
check(valid.state == CoachingState.GUIDING.value, "valid input sets coaching state")
check(valid.cancelled is False, "valid input does not cancel")

ambiguous_session = init_session(session_id="classification-smoke-ambiguous")
ambiguous = handle_user_msg(ambiguous_session.session_id, "I need help.")
check(
    ambiguous.stage == Stage.CLASSIFICATION.value,
    "ambiguous input stays in classification",
)
check(
    ambiguous.state == ClassificationState.AMBIGUOUS.value,
    "ambiguous input sets ambiguous state",
)
check(ambiguous.cancelled is False, "ambiguous input does not cancel immediately")

invalid_session = init_session(session_id="classification-smoke-invalid")
invalid = handle_user_msg(
    invalid_session.session_id,
    "Tell me the weather forecast for Rome tomorrow.",
)
check(invalid.stage == Stage.CLASSIFICATION.value, "invalid input stays in classification")
check(
    invalid.state == ClassificationState.CANCELLED.value,
    "invalid input cancels classification",
)
check(invalid.cancelled is True, "invalid input sets cancelled flag")

bounded_session = init_session(session_id="classification-smoke-bounded")
first_ambiguous = handle_user_msg(bounded_session.session_id, "I need help.")
first_ambiguous_state = first_ambiguous.state
second_ambiguous = handle_user_msg(
    bounded_session.session_id,
    "Still not sure, just help.",
)
check(
    first_ambiguous_state == ClassificationState.AMBIGUOUS.value,
    "bounded ambiguity first turn becomes ambiguous",
)
check(
    second_ambiguous.state == ClassificationState.CANCELLED.value,
    "bounded ambiguity cancels unresolved clarification",
)
check(second_ambiguous.cancelled is True, "bounded ambiguity sets cancelled flag")


print("== YAML label normalization ==")


def run_with_engine_label(label: str):
    original_evaluate = classification.evaluate
    captured_kwargs = {}

    def fake_evaluate(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "classification_label": label,
            "evaluation_message": f"Classification result: {label}.",
            "coach_message": f"Coach message for {label}.",
            "debug_message": f"fake_engine_label={label}",
        }

    classification.evaluate = fake_evaluate
    try:
        session = Session(
            session_id=f"classification-smoke-{label.lower()}",
            stage=Stage.CLASSIFICATION.value,
            state=ClassificationState.EVALUATING.value,
            user_message="Synthetic classification label normalization check.",
        )
        return classification.handle_stage(session), captured_kwargs
    finally:
        classification.evaluate = original_evaluate


valid_reply, valid_kwargs = run_with_engine_label("VALID")
check(
    valid_reply.session.state == ClassificationState.COMPLETED.value,
    "VALID label maps to completed",
)
check(valid_reply.next_stage == Stage.COACHING, "VALID label requests coaching")
check(
    "OUT_OF_SCOPE" in str(valid_kwargs.get("output_instruction", "")),
    "classification passes YAML label output instruction",
)

ambiguous_reply, _ = run_with_engine_label("AMBIGUOUS")
check(
    ambiguous_reply.session.state == ClassificationState.AMBIGUOUS.value,
    "AMBIGUOUS label maps to ambiguous",
)

out_of_scope_reply, _ = run_with_engine_label("OUT_OF_SCOPE")
check(
    out_of_scope_reply.session.state == ClassificationState.CANCELLED.value,
    "OUT_OF_SCOPE label maps to cancelled",
)
check(
    "classification_normalized_outcome=invalid"
    in str(out_of_scope_reply.session.debug_message),
    "OUT_OF_SCOPE label normalizes to internal invalid outcome",
)

distress_reply, _ = run_with_engine_label("DISTRESS")
check(
    distress_reply.session.state == ClassificationState.CANCELLED.value,
    "DISTRESS label maps to cancelled",
)
check(
    "classification_raw_outcome=distress" in str(distress_reply.session.debug_message),
    "DISTRESS label remains visible in debug output",
)

print("Classification smoke checks passed.")
PY
