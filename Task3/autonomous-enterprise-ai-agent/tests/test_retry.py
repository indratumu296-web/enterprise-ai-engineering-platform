from unittest.mock import Mock, patch

import pytest
import requests

from utils.retry import APIRequestError, request_json


def test_retries_server_error_then_returns_success():
    unavailable = Mock(status_code=503)
    unavailable.raise_for_status.side_effect = requests.HTTPError(
        "server error",
        response=unavailable,
    )
    success = Mock(status_code=200)
    success.json.return_value = {"status": "ok"}

    with (
        patch("utils.retry.requests.request", side_effect=[unavailable, success]) as request,
        patch("utils.retry.time.sleep"),
    ):
        result = request_json("GET", "http://mock.test/health")

    assert result == {"status": "ok"}
    assert request.call_count == 2


def test_does_not_retry_client_validation_error():
    bad_request = Mock(status_code=422, text="invalid request")
    bad_request.json.return_value = {"detail": "invalid request"}
    bad_request.raise_for_status.side_effect = requests.HTTPError(
        "client error",
        response=bad_request,
    )

    with patch("utils.retry.requests.request", return_value=bad_request) as request:
        with pytest.raises(APIRequestError, match="invalid request"):
            request_json("POST", "http://mock.test/tickets")

    assert request.call_count == 1
