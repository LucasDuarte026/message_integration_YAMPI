import unittest
from unittest.mock import patch, MagicMock
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.client import YampiClient

class TestYampiClientRetries(unittest.TestCase):
    def setUp(self):
        self.client = YampiClient(
            user_token="dummy_token",
            user_secret_key="dummy_secret",
            merchant_alias="test_alias"
        )

    @patch("src.core.client.time.sleep", return_value=None)
    @patch("requests.request")
    def test_request_retries_on_connection_error_and_succeeds(self, mock_request, mock_sleep):
        # Configura as duas primeiras chamadas para falhar com ConnectionError (ex: ConnectionResetError)
        # e a terceira para retornar 200 OK com payload JSON
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": [{"id": 1}]}

        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection aborted. ConnectionResetError(104)"),
            requests.exceptions.ConnectionError("Connection aborted. ConnectionResetError(104)"),
            mock_response_success
        ]

        result = self.client.request("GET", "orders")

        self.assertEqual(result, {"data": [{"id": 1}]})
        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("src.core.client.time.sleep", return_value=None)
    @patch("requests.request")
    def test_request_fails_after_3_attempts_and_raises(self, mock_request, mock_sleep):
        # Configura todas as 3 chamadas para falharem com ConnectionError
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection reset by peer")

        with self.assertRaises(requests.exceptions.ConnectionError):
            self.client.request("GET", "orders")

        self.assertEqual(mock_request.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("src.core.client.time.sleep", return_value=None)
    @patch("requests.request")
    def test_request_retries_on_http_500_and_succeeds(self, mock_request, mock_sleep):
        mock_500 = MagicMock()
        mock_500.status_code = 500

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"status": "ok"}

        mock_request.side_effect = [mock_500, mock_200]

        result = self.client.request("GET", "orders")

        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

if __name__ == "__main__":
    unittest.main()
