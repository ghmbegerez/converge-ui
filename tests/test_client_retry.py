"""Tests for ApiClient retry logic."""

from unittest.mock import patch, MagicMock

import httpx
import pytest

from converge_ui.clients.base import ApiClient


class _TestClient(ApiClient):
    service_name = "test-svc"


@pytest.fixture
def client():
    return _TestClient("http://fake:9999", timeout_seconds=1.0, retries=1, retry_delay=0.01)


class TestRetryOnServerError:
    def test_503_then_200_returns_data(self, client):
        resp_503 = MagicMock(status_code=503)
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"ok": True}
        resp_200.raise_for_status = MagicMock()

        with patch("httpx.request", side_effect=[resp_503, resp_200]):
            result = client._get("/test")

        assert result == {"ok": True}

    def test_two_503s_returns_none(self, client):
        resp_503 = MagicMock(status_code=503)
        resp_503.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503", request=MagicMock(), response=resp_503,
        )

        with patch("httpx.request", return_value=resp_503):
            result = client._get("/test")

        assert result is None

    def test_502_retried(self, client):
        resp_502 = MagicMock(status_code=502)
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"data": 1}
        resp_200.raise_for_status = MagicMock()

        with patch("httpx.request", side_effect=[resp_502, resp_200]):
            result = client._get("/path")

        assert result == {"data": 1}


class TestRetryOnConnectionError:
    def test_connect_error_retried(self, client):
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"recovered": True}
        resp_200.raise_for_status = MagicMock()

        with patch("httpx.request", side_effect=[httpx.ConnectError("refused"), resp_200]):
            result = client._get("/test")

        assert result == {"recovered": True}

    def test_connect_error_exhausted(self, client):
        with patch("httpx.request", side_effect=httpx.ConnectError("refused")):
            result = client._get("/test")

        assert result is None

    def test_read_timeout_retried(self, client):
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"ok": True}
        resp_200.raise_for_status = MagicMock()

        with patch("httpx.request", side_effect=[httpx.ReadTimeout("slow"), resp_200]):
            result = client._get("/test")

        assert result == {"ok": True}


class TestNoRetryOn4xx:
    def test_404_not_retried(self, client):
        resp_404 = MagicMock(status_code=404)
        resp_404.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=resp_404,
        )

        with patch("httpx.request", return_value=resp_404) as mock_req:
            result = client._get("/missing")

        assert result is None
        assert mock_req.call_count == 1  # NOT retried


class TestPostRetry:
    def test_post_retries_on_503(self, client):
        resp_503 = MagicMock(status_code=503)
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {"created": True}
        resp_200.raise_for_status = MagicMock()

        with patch("httpx.request", side_effect=[resp_503, resp_200]):
            result = client._post("/create", json={"key": "val"})

        assert result == {"created": True}


class TestNoRetries:
    def test_zero_retries_no_retry(self):
        c = _TestClient("http://fake:9999", retries=0, retry_delay=0.01)
        resp_503 = MagicMock(status_code=503)
        resp_503.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503", request=MagicMock(), response=resp_503,
        )

        with patch("httpx.request", return_value=resp_503) as mock_req:
            result = c._get("/test")

        assert result is None
        assert mock_req.call_count == 1
