"""Configuration loading for the input safety gate."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from backend.input_safety.models import InputSafetyConfig, InputSafetyMode


VALID_MODES: set[str] = {"off", "monitor", "block"}
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "input_safety.yaml"


DEFAULT_BLOCK_MESSAGE = (
    "I can't continue with that wording. Please rephrase your message in a way "
    "that stays appropriate for a reflective workplace coaching session."
)


def _default_config_payload() -> dict[str, Any]:
    return {
        "enabled": True,
        "mode": "block",
        "max_length": 12000,
        "repeated_character_limit": 24,
        "repeated_phrase_limit": 5,
        "default_block_message": DEFAULT_BLOCK_MESSAGE,
        "categories": {},
    }


def _mode_override() -> InputSafetyMode | None:
    raw_mode = os.getenv("GLIMPSE_INPUT_SAFETY_MODE")
    if raw_mode is None:
        return None

    mode = raw_mode.strip().lower()
    if mode not in VALID_MODES:
        return None

    return mode  # type: ignore[return-value]


def load_input_safety_config(path: Path | None = None) -> InputSafetyConfig:
    """Load safety config from YAML, applying the environment mode override."""
    config_path = path or CONFIG_PATH
    payload = _default_config_payload()

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Input safety config root must be a mapping: {config_path}")
        payload.update(loaded)

    override = _mode_override()
    if override is not None:
        payload["mode"] = override

    return InputSafetyConfig.model_validate(payload)
