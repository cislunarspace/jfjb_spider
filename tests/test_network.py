"""网络请求模块测试。"""

from __future__ import annotations

import requests
from unittest.mock import MagicMock

import pytest

from newspaper_pdf.network import (
    DEFAULT_USER_AGENT,
    REQUEST_TIMEOUT,
    create_session,
    retry_get,
)


# ── create_session ───────────────────────────────────────────────────────────


@pytest.mark.unit
class TestCreateSession:
    def test_default_user_agent(self) -> None:
        session = create_session()
        assert session.headers["User-Agent"] == DEFAULT_USER_AGENT

    def test_custom_user_agent(self) -> None:
        session = create_session(user_agent="CustomBot/1.0")
        assert session.headers["User-Agent"] == "CustomBot/1.0"

    def test_returns_session_instance(self) -> None:
        session = create_session()
        assert isinstance(session, requests.Session)


# ── retry_get ────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestRetryGet:
    def _make_response(self, status_code: int = 200) -> MagicMock:
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status_code
        if status_code >= 400:
            http_error = requests.exceptions.HTTPError(response=resp)
            resp.raise_for_status.side_effect = http_error
        else:
            resp.raise_for_status.return_value = None
        return resp

    def test_success_first_try(self, mocker) -> None:
        session = MagicMock(spec=requests.Session)
        resp = self._make_response(200)
        session.get.return_value = resp

        result = retry_get(session, "https://example.com")
        assert result is resp
        session.get.assert_called_once()

    def test_retries_on_500(self, mocker) -> None:
        mocker.patch("newspaper_pdf.network.time.sleep")
        session = MagicMock(spec=requests.Session)
        resp_500 = self._make_response(500)
        resp_200 = self._make_response(200)
        session.get.side_effect = [resp_500, resp_200]

        result = retry_get(session, "https://example.com")
        assert result is resp_200
        assert session.get.call_count == 2

    def test_no_retry_on_404(self, mocker) -> None:
        session = MagicMock(spec=requests.Session)
        resp_404 = self._make_response(404)
        session.get.return_value = resp_404

        with pytest.raises(requests.exceptions.HTTPError):
            retry_get(session, "https://example.com")
        session.get.assert_called_once()

    def test_retries_on_connection_error(self, mocker) -> None:
        mocker.patch("newspaper_pdf.network.time.sleep")
        session = MagicMock(spec=requests.Session)
        resp_200 = self._make_response(200)
        session.get.side_effect = [
            requests.exceptions.ConnectionError(),
            resp_200,
        ]

        result = retry_get(session, "https://example.com")
        assert result is resp_200

    def test_retries_on_timeout(self, mocker) -> None:
        mocker.patch("newspaper_pdf.network.time.sleep")
        session = MagicMock(spec=requests.Session)
        resp_200 = self._make_response(200)
        session.get.side_effect = [
            requests.exceptions.Timeout(),
            resp_200,
        ]

        result = retry_get(session, "https://example.com")
        assert result is resp_200

    def test_max_retries_exhausted(self, mocker) -> None:
        mocker.patch("newspaper_pdf.network.time.sleep")
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(requests.exceptions.ConnectionError):
            retry_get(session, "https://example.com", max_retries=3)
        assert session.get.call_count == 3

    def test_exponential_backoff(self, mocker) -> None:
        sleep_mock = mocker.patch("newspaper_pdf.network.time.sleep")
        session = MagicMock(spec=requests.Session)
        resp_200 = self._make_response(200)
        session.get.side_effect = [
            self._make_response(500),
            self._make_response(500),
            resp_200,
        ]

        retry_get(session, "https://example.com", backoff_factor=1.0)
        # 第一次重试等待 1.0 * 2^0 = 1.0
        # 第二次重试等待 1.0 * 2^1 = 2.0
        sleep_mock.assert_any_call(1.0)
        sleep_mock.assert_any_call(2.0)

    def test_sets_default_timeout(self, mocker) -> None:
        session = MagicMock(spec=requests.Session)
        resp = self._make_response(200)
        session.get.return_value = resp

        retry_get(session, "https://example.com")
        session.get.assert_called_once_with("https://example.com", timeout=REQUEST_TIMEOUT)

    def test_custom_timeout(self, mocker) -> None:
        session = MagicMock(spec=requests.Session)
        resp = self._make_response(200)
        session.get.return_value = resp

        retry_get(session, "https://example.com", timeout=60)
        session.get.assert_called_once_with("https://example.com", timeout=60)
