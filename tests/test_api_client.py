import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from api_client import request_json  # noqa: E402


class RequestJsonTests(unittest.TestCase):
    @patch("api_client.requests.get")
    def test_get_success_returns_parsed_json(self, mock_get: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"session_id": "abc"}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = request_json("http://api.test", "GET", "/session_initialise", timeout_seconds=12)

        mock_get.assert_called_once_with("http://api.test/session_initialise", timeout=12)
        self.assertEqual(result.data, {"session_id": "abc"})
        self.assertIsNone(result.error_message)
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.not_found)

    @patch("api_client.requests.post")
    def test_post_success_sends_json_payload_and_returns_parsed_json(self, mock_post: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"ok": True}
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        payload = {"session_id": "abc", "user_message": "hello"}
        result = request_json("http://api.test", "POST", "/user_message", payload=payload, timeout_seconds=45)

        mock_post.assert_called_once_with(
            "http://api.test/user_message",
            json=payload,
            timeout=45,
        )
        self.assertEqual(result.data, {"ok": True})
        self.assertIsNone(result.error_message)
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.not_found)

    @patch("api_client.requests.get")
    def test_request_exception_returns_error_result(self, mock_get: Mock) -> None:
        mock_get.side_effect = requests.RequestException("network unavailable")

        result = request_json("http://api.test", "GET", "/session_initialise")

        self.assertIsNone(result.data)
        self.assertEqual(result.error_message, "network unavailable")
        self.assertIsNone(result.status_code)
        self.assertFalse(result.not_found)

    @patch("api_client.requests.post")
    def test_http_error_exposes_status_code(self, mock_post: Mock) -> None:
        response = Mock()
        response.status_code = 404
        http_error = requests.HTTPError("404 Client Error: Not Found")
        http_error.response = response
        response.raise_for_status.side_effect = http_error
        mock_post.return_value = response

        result = request_json("http://api.test", "POST", "/user_message", payload={"x": "y"})

        self.assertIsNone(result.data)
        self.assertEqual(result.status_code, 404)
        self.assertTrue(result.not_found)
        self.assertEqual(result.error_message, "404 Client Error: Not Found")


if __name__ == "__main__":
    unittest.main()
