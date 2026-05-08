import sys
import unittest
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from session_state import (  # noqa: E402
    MISSING_SESSION_NOTICE,
    build_backend_turn_state_update,
    build_missing_session_reset_state,
)


class BuildBackendTurnStateUpdateTests(unittest.TestCase):
    def test_backend_coaching_response_maps_to_coaching_screen(self) -> None:
        update = build_backend_turn_state_update(
            {
                "session": {"stage": "coaching", "state": "guiding"},
                "coach_message": "Tell me more.",
            }
        )

        self.assertEqual(update["ui_screen"], "coaching")
        self.assertEqual(update["coach_message"], "Tell me more.")
        self.assertEqual(update["session_view"], {"stage": "coaching", "state": "guiding"})

    def test_backend_synthesis_response_maps_to_synthesis_review(self) -> None:
        update = build_backend_turn_state_update(
            {
                "session": {"stage": "synthesis", "state": "validating"},
                "coach_message": "Here is the synthesis.",
            }
        )

        self.assertEqual(update["ui_screen"], "synthesis_review")

    def test_backend_pathways_response_caches_pathways_message(self) -> None:
        update = build_backend_turn_state_update(
            {
                "session": {"stage": "pathways", "state": "presenting"},
                "coach_message": "## Pathway\nDetails",
            },
            current_cached_pathways_message="older",
        )

        self.assertEqual(update["cached_pathways_message"], "## Pathway\nDetails")

    def test_non_pathways_response_does_not_overwrite_cached_pathways_message(self) -> None:
        update = build_backend_turn_state_update(
            {
                "session": {"stage": "coaching", "state": "guiding"},
                "coach_message": "Next question.",
            },
            current_cached_pathways_message="existing pathways",
        )

        self.assertEqual(update["cached_pathways_message"], "existing pathways")


class BuildMissingSessionResetStateTests(unittest.TestCase):
    def test_missing_session_reset_state_returns_intro_screen(self) -> None:
        reset_state = build_missing_session_reset_state({})
        self.assertEqual(reset_state["ui_screen"], "intro")

    def test_missing_session_reset_clears_fields_and_increments_versions(self) -> None:
        reset_state = build_missing_session_reset_state(
            {
                "session_id": "abc",
                "session_view": {"stage": "coaching"},
                "coach_message": "reply",
                "cached_pathways_message": "cached",
                "debug_history": [{"turn": 1}],
                "latest_debug": {"turn": 1},
                "latest_debug_fingerprint": "fingerprint",
                "awaiting_pathways_after_refinement": True,
                "problem_input_version": 3,
                "coaching_input_version": 4,
                "synthesis_feedback_version": 5,
                "pathways_selection_version": 6,
                "frontend_error": "error",
            }
        )

        self.assertIsNone(reset_state["session_id"])
        self.assertIsNone(reset_state["session_view"])
        self.assertEqual(reset_state["coach_message"], "")
        self.assertEqual(reset_state["cached_pathways_message"], "")
        self.assertEqual(reset_state["debug_history"], [])
        self.assertIsNone(reset_state["latest_debug"])
        self.assertIsNone(reset_state["latest_debug_fingerprint"])
        self.assertFalse(reset_state["awaiting_pathways_after_refinement"])
        self.assertEqual(reset_state["problem_input_version"], 4)
        self.assertEqual(reset_state["coaching_input_version"], 5)
        self.assertEqual(reset_state["synthesis_feedback_version"], 6)
        self.assertEqual(reset_state["pathways_selection_version"], 7)
        self.assertIsNone(reset_state["frontend_error"])

    def test_missing_session_reset_includes_same_notice_text(self) -> None:
        reset_state = build_missing_session_reset_state({})
        self.assertEqual(reset_state["frontend_notice"], MISSING_SESSION_NOTICE)


if __name__ == "__main__":
    unittest.main()
