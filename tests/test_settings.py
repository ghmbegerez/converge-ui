from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from converge_ui.config.settings import load_settings


def test_load_settings_defaults() -> None:
    with patch.dict(os.environ, {}, clear=True):
        settings = load_settings()
    assert settings.environment == "local"
    assert settings.data_mode == "hybrid"
    assert settings.allow_fallback_ui is True
    assert settings.rate_limit_enabled is True
    assert settings.trust_proxy_headers is False


def test_production_disables_fallback_by_default() -> None:
    with patch.dict(os.environ, {"CONVERGE_UI_ENV": "production"}, clear=True):
        settings = load_settings()
    assert settings.environment == "production"
    assert settings.allow_fallback_ui is False
    assert settings.trust_proxy_headers is True


def test_invalid_data_mode_raises() -> None:
    with patch.dict(os.environ, {"CONVERGE_UI_DATA_MODE": "broken"}, clear=True):
        with pytest.raises(ValueError, match="Invalid CONVERGE_UI_DATA_MODE"):
            load_settings()


def test_invalid_rate_limit_rpm_raises() -> None:
    with patch.dict(os.environ, {"CONVERGE_UI_RATE_LIMIT_RPM": "0"}, clear=True):
        with pytest.raises(ValueError, match="RATE_LIMIT_RPM"):
            load_settings()


def test_frontend_dist_can_be_overridden() -> None:
    custom = str(Path("/tmp/converge-ui-dist"))
    with patch.dict(os.environ, {"CONVERGE_UI_FRONTEND_DIST": custom}, clear=True):
        settings = load_settings()
    assert settings.frontend_dist_dir == Path(custom)
