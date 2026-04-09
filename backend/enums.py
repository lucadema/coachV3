"""
Enumerations for Coach V3.

This module defines the global macro-stage enum, the local state enums owned by
each stage, and the chat role enum used by chat history models.
"""

from enum import Enum


class Stage(str, Enum):
    """Macro-stages for the end-to-end cognitive process."""

    CLASSIFICATION = "classification"
    COACHING = "coaching"
    SYNTHESIS = "synthesis"
    PATHWAYS = "pathways"
    CLOSURE = "closure"


class StateType(str, Enum):
    """Execution behaviour types for local stage states."""

    EVALUATIVE = "evaluative"
    PRODUCTION = "production"
    WAITING = "waiting"
    TERMINAL = "terminal"


class ClassificationState(str, Enum):
    """Local states for the Classification stage."""

    EVALUATING = "evaluating"
    AMBIGUOUS = "ambiguous"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CoachingState(str, Enum):
    """Local states for the Coaching stage."""

    GUIDING = "guiding"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SynthesisState(str, Enum):
    """Local states for the Synthesis stage."""

    PREPARING = "preparing"
    VALIDATING = "validating"
    REFINING = "refining"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PathwaysState(str, Enum):
    """Local states for the Pathways stage."""

    PREPARING = "preparing"
    PRESENTING = "presenting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ClosureState(str, Enum):
    """Local states for the Closure stage."""

    PREPARING = "preparing"
    COMPLETED = "completed"


class ChatRole(str, Enum):
    """Visible chat roles stored in session chat history."""

    USER = "user"
    ASSISTANT = "assistant"
