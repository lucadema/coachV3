"""Rule evaluation for deterministic input safety checks."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from backend.input_safety.models import (
    InputSafetyCategoryConfig,
    InputSafetyConfig,
    InputSafetyResult,
)


GENERIC_BLOCK_MESSAGE = (
    "I can't continue with that wording. Please rephrase your message in a way "
    "that stays appropriate for a reflective workplace coaching session."
)


def normalize_text(text: str | None) -> str:
    """Normalize user text for deterministic matching."""
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\u2019", "'").replace("\u2018", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
    return " ".join(normalized.casefold().split())


def _result(
    *,
    config: InputSafetyConfig,
    category: str | None = None,
    category_config: InputSafetyCategoryConfig | None = None,
    reason_code: str | None = None,
    debug: dict | None = None,
) -> InputSafetyResult:
    mode = "off" if not config.enabled else config.mode
    action = category_config.action if category_config else "block"
    blocked = bool(mode == "block" and action == "block" and category is not None)
    user_message = None

    if blocked:
        user_message = (
            category_config.user_message
            if category_config and category_config.user_message
            else config.default_block_message
            or GENERIC_BLOCK_MESSAGE
        )

    return InputSafetyResult(
        allowed=not blocked,
        blocked=blocked,
        mode=mode,
        category=category,
        severity=category_config.severity if category_config else None,
        reason_code=reason_code,
        user_message=user_message,
        debug=debug,
    )


def _allow(config: InputSafetyConfig, debug: dict | None = None) -> InputSafetyResult:
    mode = "off" if not config.enabled else config.mode
    return InputSafetyResult(
        allowed=True,
        blocked=False,
        mode=mode,
        debug=debug,
    )


def _category(config: InputSafetyConfig, name: str) -> InputSafetyCategoryConfig | None:
    category = config.categories.get(name)
    if category is None or not category.enabled:
        return None
    return category


def _deterministic_result(
    config: InputSafetyConfig,
    category_name: str,
    reason_code: str,
    debug: dict,
) -> InputSafetyResult | None:
    category_config = _category(config, category_name)
    if category_config is None:
        return None
    return _result(
        config=config,
        category=category_name,
        category_config=category_config,
        reason_code=reason_code,
        debug=debug,
    )


def _has_repeated_phrase_spam(text: str, limit: int) -> bool:
    words = re.findall(r"[a-z0-9']+", text)
    if len(words) < limit:
        return False

    for size in range(1, 5):
        phrases = [" ".join(words[index : index + size]) for index in range(len(words) - size + 1)]
        counts = Counter(phrases)
        if any(count >= limit for count in counts.values()):
            return True

    return False


def _pattern_matches(pattern: str, normalized_text: str) -> bool:
    try:
        return re.search(pattern, normalized_text, flags=re.IGNORECASE) is not None
    except re.error:
        return pattern.casefold() in normalized_text


def evaluate_rules(
    text: str,
    config: InputSafetyConfig,
    context: dict | None = None,
) -> InputSafetyResult:
    """Evaluate deterministic checks and configured category patterns."""
    mode = "off" if not config.enabled else config.mode
    if mode == "off":
        return _allow(config, debug={"mode": mode})

    normalized = normalize_text(text)
    context = context or {}

    if not normalized:
        result = _deterministic_result(
            config,
            "spam_or_nonsense",
            "empty_input",
            {
                "rule_type": "deterministic",
                "stage": context.get("stage"),
                "state": context.get("state"),
            },
        )
        if result is not None:
            return result

    if config.max_length > 0 and len(text or "") > config.max_length:
        result = _deterministic_result(
            config,
            "spam_or_nonsense",
            "input_too_long",
            {
                "rule_type": "deterministic",
                "limit": config.max_length,
                "stage": context.get("stage"),
                "state": context.get("state"),
            },
        )
        if result is not None:
            return result

    if config.repeated_character_limit > 0:
        repeated_character_pattern = r"(.)\1{" + str(config.repeated_character_limit) + r",}"
        if re.search(repeated_character_pattern, normalized):
            result = _deterministic_result(
                config,
                "spam_or_nonsense",
                "repeated_character_spam",
                {
                    "rule_type": "deterministic",
                    "limit": config.repeated_character_limit,
                    "stage": context.get("stage"),
                    "state": context.get("state"),
                },
            )
            if result is not None:
                return result

    if config.repeated_phrase_limit > 0 and _has_repeated_phrase_spam(
        normalized,
        config.repeated_phrase_limit,
    ):
        result = _deterministic_result(
            config,
            "spam_or_nonsense",
            "repeated_phrase_spam",
            {
                "rule_type": "deterministic",
                "limit": config.repeated_phrase_limit,
                "stage": context.get("stage"),
                "state": context.get("state"),
            },
        )
        if result is not None:
            return result

    for category_name, category_config in config.categories.items():
        if not category_config.enabled:
            continue

        for index, pattern in enumerate(category_config.patterns):
            if _pattern_matches(pattern, normalized):
                return _result(
                    config=config,
                    category=category_name,
                    category_config=category_config,
                    reason_code=f"{category_name}_pattern",
                    debug={
                        "rule_type": "configured_pattern",
                        "rule_index": index,
                        "stage": context.get("stage"),
                        "state": context.get("state"),
                    },
                )

    return _allow(config, debug={"mode": mode})
