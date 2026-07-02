"""Models for deterministic input safety checks."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


InputSafetyMode = Literal["off", "monitor", "block"]
InputSafetyAction = Literal["allow", "monitor", "block"]
InputSafetySeverity = Literal["low", "medium", "high"]


class InputSafetyCategoryConfig(BaseModel):
    """Configuration for one safety category."""

    enabled: bool = True
    severity: InputSafetySeverity = "medium"
    action: InputSafetyAction = "block"
    patterns: list[str] = Field(default_factory=list)
    user_message: str


class InputSafetyConfig(BaseModel):
    """Top-level input safety configuration."""

    enabled: bool = True
    mode: InputSafetyMode = "block"
    max_length: int = 12000
    repeated_character_limit: int = 24
    repeated_phrase_limit: int = 5
    default_block_message: str
    categories: dict[str, InputSafetyCategoryConfig] = Field(default_factory=dict)


class InputSafetyResult(BaseModel):
    """Structured result returned by the deterministic safety gate."""

    allowed: bool
    blocked: bool
    mode: InputSafetyMode
    category: str | None = None
    severity: InputSafetySeverity | None = None
    reason_code: str | None = None
    user_message: str | None = None
    debug: dict[str, Any] | None = None
