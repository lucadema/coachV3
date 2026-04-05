"""
Data models for Coach V3.

This module keeps only the models that add real value at a boundary or in the
internal domain model.

Design rule for this POC:
- use plain function parameters and return values when only a single object or
  single parameter is exchanged
- define models only when they add clarity, validation, or a real contract

Contents:
1. Core internal models
2. API-facing models
3. Stage module contract
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from backend.enums import ChatRole, Stage


# ============================================================================
# Core internal models
# ============================================================================

class ChatMessage(BaseModel):
    """A single visible chat message stored in session chat history."""

    role: ChatRole
    message: str


class Session(BaseModel):
    """
    Canonical session object carried across the backend.

    Ownership:
    - controller.py owns loading and persistence
    - stage modules and engine.py operate on the in-memory session provided by
      controller.py

    Notes:
    - stage is the macro-stage
    - state is the current local state of the active stage
    """

    session_id: str
    stage: str
    state: str

    user_message: str | None = None
    evaluation_message: str | None = None
    coach_message: str | None = None
    debug_message: str | None = None

    chat_history: list[ChatMessage] = Field(default_factory=list)
    stage_context: dict[str, Any] = Field(default_factory=dict)

    cancelled: bool = False
    completed: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# API-facing models
# Boundary: frontend app.py <-> backend api.py
# ============================================================================

class SessionView(BaseModel):
    """
    Reduced frontend-safe view of the internal session.

    The frontend should not receive the full internal Session object.
    """

    session_id: str
    stage: Stage
    state: str
    cancelled: bool = False
    completed: bool = False


class UserMsg(BaseModel):
    """Request payload sent by the frontend when submitting a user message."""

    session_id: str
    user_message: str


class UserMsgReply(BaseModel):
    """
    Reply returned by the API user message endpoint.

    Only the minimum useful information is returned:
    - updated session view
    - latest user-facing coach message
    """

    session: SessionView
    coach_message: str | None = None


class DebugReply(BaseModel):
    """
    Reply returned by the API debug endpoint.

    Debug data stays on a dedicated endpoint rather than being mixed into
    normal user-turn replies.
    """

    session: SessionView
    debug_message: str | None = None


# ============================================================================
# Stage module contract
# Boundary: controller.py <-> stage modules
# ============================================================================

class StageReply(BaseModel):
    """
    Reply returned by a stage module.

    Rules:
    - session contains the updated in-memory session
    - next_stage requests a macro-stage transition
    - if next_stage is None, controller keeps the current macro-stage unless
      the updated session itself has been cancelled or completed
    """

    session: Session
    next_stage: Stage | None = None
