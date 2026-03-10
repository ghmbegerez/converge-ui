from __future__ import annotations

from starlette.requests import Request

from converge_ui.http import client_ip_for_request


def make_request(headers: list[tuple[bytes, bytes]]) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "client": ("10.0.0.10", 1234),
        "scheme": "http",
        "server": ("test", 80),
        "query_string": b"",
    }
    return Request(scope)


def test_client_ip_uses_socket_by_default() -> None:
    request = make_request([])
    assert client_ip_for_request(request, trust_proxy_headers=False) == "10.0.0.10"


def test_client_ip_uses_x_forwarded_for_when_trusted() -> None:
    request = make_request([(b"x-forwarded-for", b"203.0.113.5, 10.0.0.10")])
    assert client_ip_for_request(request, trust_proxy_headers=True) == "203.0.113.5"
