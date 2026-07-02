"""Public service API for the deterministic input safety gate."""

from __future__ import annotations

from backend.input_safety.config import load_input_safety_config
from backend.input_safety.models import InputSafetyResult
from backend.input_safety.rules import evaluate_rules


def evaluate_input_safety(
    text: str,
    context: dict | None = None,
) -> InputSafetyResult:
    """Evaluate user input safety through the self-contained rule module."""
    config = load_input_safety_config()
    return evaluate_rules(text=text, config=config, context=context)
