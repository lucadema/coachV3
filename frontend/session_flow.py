"""Pure frontend flow helpers for the Streamlit migration path.

These helpers intentionally avoid any dependency on Streamlit, HTTP calls,
or session_state so they can be tested in isolation and later reused by the
React frontend.
"""

from __future__ import annotations

import re
from typing import Any


_BACKEND_STAGE_TO_SCREEN = {
    "classification": "coaching",
    "coaching": "coaching",
    "synthesis": "synthesis_review",
    "pathways": "pathways",
    "closure": "feedback",
}


def map_backend_to_screen(session: dict[str, Any]) -> str:
    """Translate the backend macro-stage into the current frontend screen."""
    return _BACKEND_STAGE_TO_SCREEN.get(session.get("stage"), "coaching")


def is_refined_synthesis_waiting_for_pathways(session: dict[str, Any]) -> bool:
    """Detect the backend state used after synthesis refinement."""
    return (
        session.get("stage") == "pathways"
        and session.get("state") == "preparing"
    )


def parse_pathway_cards(text: str | None) -> list[dict[str, str]]:
    """Extract pathway cards from markdown headings of the form ``## Title``."""
    source = str(text or "").strip()
    if not source:
        return []

    heading_matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", source))
    if not heading_matches:
        return []

    cards: list[dict[str, str]] = []
    for index, match in enumerate(heading_matches):
        title = match.group(1).strip()
        body_start = match.end()
        body_end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(source)
        )
        body = source[body_start:body_end].strip()
        if not title or not body:
            continue
        cards.append({"title": title, "body": body})

    return cards
