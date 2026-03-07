from __future__ import annotations

import sys
from pathlib import Path

import pytest

from fileclassifier.webapi.utils.pathing import (
    API_PROJECT_ROOT,
    reset_runtime_default_paths_cache,
    resolve_path,
    runtime_default_paths,
)


@pytest.fixture(autouse=True)
def _reset_runtime_defaults_cache():
    reset_runtime_default_paths_cache()
    yield
    reset_runtime_default_paths_cache()


def test_runtime_default_paths_for_development(monkeypatch) -> None:
    monkeypatch.delenv("FILECLASSIFIER_DESKTOP_MODE", raising=False)
    monkeypatch.delenv("FILECLASSIFIER_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    defaults = runtime_default_paths()

    assert defaults.mode == "development"
    assert defaults.base_dir == API_PROJECT_ROOT / "data"
    assert defaults.input_dir == API_PROJECT_ROOT / "data" / "input"
    assert defaults.output_dir == API_PROJECT_ROOT / "data" / "output"
    assert defaults.logs_dir == API_PROJECT_ROOT / "data" / "logs"


def test_runtime_default_paths_for_desktop_mode_with_explicit_dir(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime-root"
    monkeypatch.setenv("FILECLASSIFIER_DESKTOP_MODE", "1")
    monkeypatch.setenv("FILECLASSIFIER_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    defaults = runtime_default_paths()

    assert defaults.mode == "desktop"
    assert defaults.base_dir == runtime_dir
    assert defaults.excel_base_dir == runtime_dir / "excel"
    assert defaults.input_dir == runtime_dir / "input"
    assert defaults.output_dir == runtime_dir / "output"
    assert defaults.logs_dir == runtime_dir / "logs"
    assert defaults.excel_base_dir.is_dir()
    assert defaults.input_dir.is_dir()
    assert defaults.output_dir.is_dir()
    assert defaults.logs_dir.is_dir()


def test_resolve_path_prefers_runtime_base_for_relative_paths(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime-root"
    monkeypatch.setenv("FILECLASSIFIER_DESKTOP_MODE", "1")
    monkeypatch.setenv("FILECLASSIFIER_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    resolved = resolve_path("output")

    assert resolved == runtime_dir / "output"
