import sys
import unittest
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from session_flow import (  # noqa: E402
    is_refined_synthesis_waiting_for_pathways,
    map_backend_to_screen,
    parse_pathway_cards,
)


class MapBackendToScreenTests(unittest.TestCase):
    def test_classification_maps_to_coaching(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "classification"}), "coaching")

    def test_coaching_maps_to_coaching(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "coaching"}), "coaching")

    def test_synthesis_maps_to_synthesis_review(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "synthesis"}), "synthesis_review")

    def test_pathways_maps_to_pathways(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "pathways"}), "pathways")

    def test_closure_maps_to_feedback(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "closure"}), "feedback")

    def test_unknown_stage_defaults_to_coaching(self) -> None:
        self.assertEqual(map_backend_to_screen({"stage": "fallback"}), "coaching")


class RefinedSynthesisWaitingTests(unittest.TestCase):
    def test_pathways_preparing_is_detected(self) -> None:
        session = {"stage": "pathways", "state": "preparing"}
        self.assertTrue(is_refined_synthesis_waiting_for_pathways(session))

    def test_pathways_other_state_is_not_detected(self) -> None:
        session = {"stage": "pathways", "state": "presenting"}
        self.assertFalse(is_refined_synthesis_waiting_for_pathways(session))


class ParsePathwayCardsTests(unittest.TestCase):
    def test_markdown_headings_are_parsed_into_cards(self) -> None:
        text = """
Intro text

## Pathway one
Body for the first pathway.

## Pathway two
Body for the second pathway.
""".strip()

        self.assertEqual(
            parse_pathway_cards(text),
            [
                {"title": "Pathway one", "body": "Body for the first pathway."},
                {"title": "Pathway two", "body": "Body for the second pathway."},
            ],
        )

    def test_text_without_headings_returns_empty_list(self) -> None:
        self.assertEqual(parse_pathway_cards("No headings here."), [])


if __name__ == "__main__":
    unittest.main()
