"""Tests for API key authentication middleware."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from converge_ui.api.auth import (
    Principal,
    init_auth,
    minimum_role_for,
    resolve_principal,
)


class TestPrincipal:
    def test_viewer_has_viewer_role(self) -> None:
        p = Principal(actor="alice", role="viewer")
        assert p.has_role("viewer")
        assert not p.has_role("operator")
        assert not p.has_role("admin")

    def test_operator_has_viewer_and_operator(self) -> None:
        p = Principal(actor="bob", role="operator")
        assert p.has_role("viewer")
        assert p.has_role("operator")
        assert not p.has_role("admin")

    def test_admin_has_all_roles(self) -> None:
        p = Principal(actor="charlie", role="admin")
        assert p.has_role("viewer")
        assert p.has_role("operator")
        assert p.has_role("admin")

    def test_to_dict(self) -> None:
        p = Principal(actor="alice", role="viewer")
        assert p.to_dict() == {"actor": "alice", "role": "viewer"}


class TestInitAuth:
    def test_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            init_auth()
            principal = resolve_principal(None)
            assert principal is not None
            assert principal.actor == "anonymous"
            assert principal.role == "admin"

    def test_enabled_with_keys(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "secret123:operator:alice,admin456:admin:bob",
        }
        with patch.dict(os.environ, env, clear=True):
            init_auth()
            principal = resolve_principal("secret123")
            assert principal is not None
            assert principal.actor == "alice"
            assert principal.role == "operator"

    def test_bearer_prefix_accepted(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "mykey:admin:root",
        }
        with patch.dict(os.environ, env, clear=True):
            init_auth()
            principal = resolve_principal("Bearer mykey")
            assert principal is not None
            assert principal.actor == "root"

    def test_invalid_key_raises(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "valid:operator:alice",
        }
        with patch.dict(os.environ, env, clear=True):
            init_auth()
            with pytest.raises(ValueError, match="Invalid API key"):
                resolve_principal("wrong-key")

    def test_missing_header_raises(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "valid:operator:alice",
        }
        with patch.dict(os.environ, env, clear=True):
            init_auth()
            with pytest.raises(ValueError, match="Missing Authorization"):
                resolve_principal(None)

    def test_malformed_keys_skipped(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "notenough,valid:operator:alice,badrole:fake:bob",
        }
        with patch.dict(os.environ, env, clear=True):
            init_auth()
            principal = resolve_principal("valid")
            assert principal is not None
            assert principal.actor == "alice"


class TestMinimumRoleFor:
    def test_get_overview_is_viewer(self) -> None:
        assert minimum_role_for("GET", "/api/v1/overview") == "viewer"

    def test_post_refresh_is_operator(self) -> None:
        assert minimum_role_for("POST", "/api/v1/actions/refresh") == "operator"

    def test_post_review_actions_are_operator(self) -> None:
        assert minimum_role_for("POST", "/api/v1/actions/reviews") == "operator"
        assert minimum_role_for("POST", "/api/v1/actions/reviews/r1/assign") == "operator"
        assert minimum_role_for("POST", "/api/v1/actions/reviews/r1/complete") == "operator"

    def test_unknown_route_defaults_to_admin(self) -> None:
        assert minimum_role_for("DELETE", "/api/v1/something") == "admin"
