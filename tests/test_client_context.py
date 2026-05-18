import unittest

from backend.client_context import extract_session_label, sanitize_session_label


class ClientContextTests(unittest.TestCase):
    def test_sanitizes_valid_session_label(self) -> None:
        self.assertEqual(sanitize_session_label(" Luca.Test-1_ "), "luca.test-1_")

    def test_rejects_invalid_session_labels(self) -> None:
        for value in ("", "this is invalid", "luca@example.com", "a" * 65, None, 123):
            with self.subTest(value=value):
                self.assertIsNone(sanitize_session_label(value))

    def test_extracts_supported_casing(self) -> None:
        self.assertEqual(extract_session_label({"session_label": "demo"}), "demo")
        self.assertEqual(extract_session_label({"sessionLabel": "Internal"}), "internal")

    def test_extract_never_raises_for_malformed_context(self) -> None:
        self.assertIsNone(extract_session_label(None))
        self.assertIsNone(extract_session_label(["session_label", "demo"]))


if __name__ == "__main__":
    unittest.main()
