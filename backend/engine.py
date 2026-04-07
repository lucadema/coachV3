"""
LLM interaction scaffold for Coach V3.

Engine is responsible for prompt construction, execution against the LLM, and
turn-specific validation/parsing.

For this first functional slice, Classification uses a YAML-backed prompt plus
deterministic parsing heuristics so the flow is testable without live network
LLM calls.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from backend.models import Session


CONFIG_DIR = Path(__file__).resolve().parent / "config"

DEFAULT_CLASSIFICATION_CONFIG: dict[str, Any] = {
    "prompt": {
        "system": (
            "You are classifying whether the user's opening message should "
            "enter the Coach V3 flow."
        ),
        "output_schema": "outcome: valid | ambiguous | invalid",
    },
    "state_instructions": {
        "evaluating": (
            "Decide whether the opening message contains a concrete coaching "
            "issue with enough context to begin."
        ),
        "ambiguous": (
            "Treat this as the user's one clarification attempt. If it still "
            "does not identify a concrete coaching issue, reject it."
        ),
    },
    "criteria": {
        "valid": "A coaching-suitable challenge with enough context.",
        "ambiguous": "Potentially relevant but too vague or too short.",
        "invalid": "Outside the coaching flow.",
    },
    "heuristics": {
        "min_words_for_valid": 6,
        "first_person_tokens": ["i", "i'm", "im", "me", "my"],
        "coaching_keywords": [
            "work",
            "career",
            "manager",
            "team",
            "relationship",
            "conflict",
            "stress",
            "overwhelmed",
            "decision",
            "decide",
        ],
        "ambiguous_keywords": [
            "help",
            "advice",
            "stuck",
            "unsure",
            "not sure",
            "something",
            "issue",
            "problem",
        ],
        "invalid_keywords": [
            "weather",
            "joke",
            "recipe",
            "sports score",
            "stock price",
            "movie review",
            "trivia",
        ],
    },
    "outputs": {
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
    },
}


class Engine:
    """Minimal engine with real support for the Classification slice."""

    def _load_stage_config(self, stage: str) -> tuple[dict[str, Any], str]:
        """Load YAML config for a stage and surface fallback details explicitly."""
        config_path = CONFIG_DIR / f"{stage}.yaml"

        try:
            with config_path.open("r", encoding="utf-8") as file:
                payload = yaml.safe_load(file) or {}

            if not isinstance(payload, dict):
                raise ValueError("YAML root must be a mapping")

            return payload, f"config_status=loaded config_path={config_path}"
        except Exception as exc:
            fallback = (
                DEFAULT_CLASSIFICATION_CONFIG if stage == "classification" else {}
            )
            return (
                fallback,
                (
                    "config_status=fallback "
                    f"config_path={config_path} "
                    f"config_error={exc!r}"
                ),
            )

    def build_prompt(self, session: Session) -> str:
        """
        Build a prompt string from session context.

        Classification now uses YAML-backed prompt/config assets; other stages
        still fall back to a simple scaffold prompt.
        """
        match session.stage:
            case "classification":
                config, _ = self._load_stage_config("classification")
                return self._build_classification_prompt(session, config)

            case _:
                return (
                    f"stage={session.stage}\n"
                    f"state={session.state}\n"
                    f"user_message={session.user_message}"
                )

    def _build_classification_prompt(
        self,
        session: Session,
        config: dict[str, Any],
    ) -> str:
        """Build the first real stage-specific prompt from YAML plus session data."""
        prompt_config = config.get("prompt", {})
        state_instructions = config.get("state_instructions", {})
        criteria = config.get("criteria", {})

        criteria_lines = "\n".join(
            f"- {name}: {description}"
            for name, description in criteria.items()
        )
        chat_history = "No prior chat history."
        if session.chat_history:
            chat_history = "\n".join(
                f"{message.role.value}: {message.message}"
                for message in session.chat_history[-6:]
            )

        return "\n\n".join(
            [
                str(prompt_config.get("system", "")),
                f"current_state: {session.state}",
                str(state_instructions.get(session.state, "")),
                "classification_criteria:",
                criteria_lines,
                "output_schema:",
                str(prompt_config.get("output_schema", "")),
                "chat_history:",
                chat_history,
                f"latest_user_message: {session.user_message or ''}",
            ]
        )

    def _classify_with_rules(
        self,
        user_message: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a deterministic classification result for the first real slice."""
        heuristics = config.get("heuristics", {})
        normalized = " ".join((user_message or "").strip().lower().split())
        tokens = re.findall(r"[a-z']+", normalized)

        min_words_for_valid = int(heuristics.get("min_words_for_valid", 6))
        first_person_tokens = set(heuristics.get("first_person_tokens", []))
        coaching_keywords = list(heuristics.get("coaching_keywords", []))
        ambiguous_keywords = list(heuristics.get("ambiguous_keywords", []))
        invalid_keywords = list(heuristics.get("invalid_keywords", []))

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
        has_first_person = any(token in first_person_tokens for token in tokens)

        if matched_invalid_keyword:
            outcome = "invalid"
            reason = (
                "matched invalid topic keyword "
                f"'{matched_invalid_keyword}'"
            )
        elif len(tokens) < min_words_for_valid:
            outcome = "ambiguous"
            reason = (
                f"message only contains {len(tokens)} word(s), which is below "
                f"the valid threshold of {min_words_for_valid}"
            )
        elif matched_coaching_keyword:
            outcome = "valid"
            reason = (
                "matched coaching keyword "
                f"'{matched_coaching_keyword}' with enough detail"
            )
        elif matched_ambiguous_keyword and len(tokens) < (min_words_for_valid + 3):
            outcome = "ambiguous"
            reason = (
                "matched ambiguity keyword "
                f"'{matched_ambiguous_keyword}' and still lacks context"
            )
        elif has_first_person and len(tokens) >= min_words_for_valid:
            outcome = "valid"
            reason = "contains first-person context and enough detail"
        else:
            outcome = "ambiguous"
            reason = "message does not yet clearly describe a coaching issue"

        return {
            "outcome": outcome,
            "reason": reason,
            "token_count": len(tokens),
            "matched_invalid_keyword": matched_invalid_keyword,
            "matched_ambiguous_keyword": matched_ambiguous_keyword,
            "matched_coaching_keyword": matched_coaching_keyword,
        }

    def classify(self, session: Session) -> dict[str, str]:
        """Classify the current opening message for the Classification stage."""
        config, config_debug = self._load_stage_config("classification")
        prompt = self._build_classification_prompt(session, config)
        outputs = config.get("outputs", {})
        prompt_preview = " ".join(prompt.split())
        if len(prompt_preview) > 240:
            prompt_preview = f"{prompt_preview[:240]}..."

        try:
            parsed = self._classify_with_rules(session.user_message or "", config)
            outcome = str(parsed["outcome"])
            evaluation_template = outputs.get(outcome, {}).get(
                "evaluation",
                f"Classification result: {outcome}.",
            )
            coach_template = outputs.get(outcome, {}).get(
                "coach",
                "No coach message configured.",
            )

            debug_lines = [
                "classification_engine=heuristic_v1",
                config_debug,
                f"classification_state_in={session.state}",
                f"user_message_length={len(session.user_message or '')}",
                f"token_count={parsed['token_count']}",
                "parse_status=ok",
                f"classification_outcome={outcome}",
                f"classification_reason={parsed['reason']}",
                (
                    "matched_invalid_keyword="
                    f"{parsed['matched_invalid_keyword'] or 'none'}"
                ),
                (
                    "matched_ambiguous_keyword="
                    f"{parsed['matched_ambiguous_keyword'] or 'none'}"
                ),
                (
                    "matched_coaching_keyword="
                    f"{parsed['matched_coaching_keyword'] or 'none'}"
                ),
                f"prompt_preview={prompt_preview}",
            ]

            return {
                "outcome": outcome,
                "evaluation_message": (
                    f"{evaluation_template} Reason: {parsed['reason']}."
                ),
                "coach_message": str(coach_template),
                "debug_message": "\n".join(debug_lines),
            }
        except Exception as exc:
            fallback_evaluation = outputs.get("ambiguous", {}).get(
                "evaluation",
                (
                    "Classification result: ambiguous. The opening message "
                    "could not be parsed cleanly."
                ),
            )
            fallback_coach = outputs.get("ambiguous", {}).get(
                "coach",
                "Please restate the coaching issue in one clearer sentence.",
            )

            return {
                "outcome": "ambiguous",
                "evaluation_message": (
                    f"{fallback_evaluation} Reason: fallback triggered because "
                    f"classification parsing failed with {exc!r}."
                ),
                "coach_message": str(fallback_coach),
                "debug_message": "\n".join(
                    [
                        "classification_engine=heuristic_v1",
                        config_debug,
                        f"classification_state_in={session.state}",
                        "parse_status=fallback_due_to_error",
                        f"classification_error={exc!r}",
                        "classification_outcome=ambiguous",
                        f"prompt_preview={prompt_preview}",
                    ]
                ),
            }

    def evaluate(self, session: Session) -> str:
        """Return the latest evaluation message supported by the engine."""
        match session.stage:
            case "classification":
                return self.classify(session)["evaluation_message"]

            case _:
                _ = self.build_prompt(session)
                return "TODO: engine evaluation not implemented yet."

    def coach(self, session: Session) -> str:
        """Return the latest coach-facing message supported by the engine."""
        match session.stage:
            case "classification":
                return self.classify(session)["coach_message"]

            case _:
                _ = self.build_prompt(session)
                return "TODO: engine coach message not implemented yet."


engine = Engine()
