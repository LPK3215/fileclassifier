from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

EXCEL_FILE_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm"}
API_PROJECT_ROOT = Path(__file__).resolve().parents[4]
APP_NAME = "FileClassifier"


@dataclass(frozen=True, slots=True)
class RuntimeDefaultPaths:
    mode: str
    base_dir: Path
    excel_base_dir: Path
    input_dir: Path
    output_dir: Path
    logs_dir: Path


def _is_truthy(raw_value: str | None) -> bool:
    return str(raw_value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_desktop_runtime() -> bool:
    if _is_truthy(os.getenv("FILECLASSIFIER_DESKTOP_MODE")):
        return True
    return bool(getattr(sys, "frozen", False))


def _explicit_runtime_base_dir() -> Path | None:
    raw_path = os.getenv("FILECLASSIFIER_RUNTIME_DIR", "").strip()
    if not raw_path:
        return None
    return Path(raw_path).expanduser()


def _fallback_runtime_root() -> Path:
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA", "").strip()
        if base:
            return Path(base) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def _executable_dir() -> Path:
    executable = Path(sys.executable)
    try:
        executable = executable.resolve()
    except OSError:
        pass
    return executable.parent


def _ensure_writable_dir(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def _select_runtime_base_dir() -> tuple[str, Path]:
    explicit = _explicit_runtime_base_dir()
    if explicit and _ensure_writable_dir(explicit):
        mode = "desktop" if _is_desktop_runtime() else "development"
        return mode, explicit

    if _is_desktop_runtime():
        if getattr(sys, "frozen", False):
            preferred = _executable_dir() / "workspace"
        else:
            preferred = API_PROJECT_ROOT / ".runtime" / "workspace"
        if _ensure_writable_dir(preferred):
            return "desktop", preferred

        fallback = _fallback_runtime_root() / "workspace"
        fallback.mkdir(parents=True, exist_ok=True)
        return "desktop", fallback

    base_dir = API_PROJECT_ROOT / "data"
    base_dir.mkdir(parents=True, exist_ok=True)
    return "development", base_dir


@lru_cache(maxsize=1)
def runtime_default_paths() -> RuntimeDefaultPaths:
    mode, base_dir = _select_runtime_base_dir()
    excel_base_dir = base_dir if mode == "development" else base_dir / "excel"
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    logs_dir = base_dir / "logs"

    for path in (excel_base_dir, input_dir, output_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    return RuntimeDefaultPaths(
        mode=mode,
        base_dir=base_dir,
        excel_base_dir=excel_base_dir,
        input_dir=input_dir,
        output_dir=output_dir,
        logs_dir=logs_dir,
    )


def reset_runtime_default_paths_cache() -> None:
    runtime_default_paths.cache_clear()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path

    defaults = runtime_default_paths()
    runtime_candidate = defaults.base_dir / path
    if runtime_candidate.exists():
        return runtime_candidate

    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate

    project_candidate = API_PROJECT_ROOT / path
    if project_candidate.exists():
        return project_candidate

    return runtime_candidate


def list_excel_files(directory: Path) -> list[str]:
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    cwd = Path.cwd()
    files: list[str] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in EXCEL_FILE_SUFFIXES:
            continue

        try:
            normalized = path.relative_to(cwd).as_posix()
        except ValueError:
            normalized = str(path)
        files.append(normalized)

    return sorted(files, key=str.lower)
