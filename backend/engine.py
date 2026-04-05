"""
LLM interaction scaffold for Coach V3.

Engine is responsible for prompt construction, execution against the LLM, and
turn-specific validation/parsing. In this first scaffold it only returns
placeholder values.
"""

from backend.models import Session


class Engine:
    """Minimal scaffold for prompt construction and LLM interaction."""

    def build_prompt(self, session: Session) -> str:
        """
        Build a placeholder prompt string from session context.

        Future implementation should concatenate:
        - chat history
        - stage context
        - state context
        - YAML prompt fragments / criteria / metadata
        """
        return (
            f"stage={session.stage}\n"
            f"state={session.state}\n"
            f"user_message={session.user_message}"
        )

    def evaluate(self, session: Session) -> str:
        """Return a placeholder evaluation message."""
        _ = self.build_prompt(session)
        return "TODO: engine evaluation not implemented yet."

    def coach(self, session: Session) -> str:
        """Return a placeholder coach message."""
        _ = self.build_prompt(session)
        return "TODO: engine coach message not implemented yet."


engine = Engine()
