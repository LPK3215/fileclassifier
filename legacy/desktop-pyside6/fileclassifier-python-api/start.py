from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
RELAUNCH_FLAG = "--__fileclassifier_relaunched"


def _venv_python_path() -> Path:
    if os.name == "nt":
        return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".venv" / "bin" / "python"


def _relaunch_with_venv_if_available() -> None:
    if RELAUNCH_FLAG in sys.argv:
        return

    venv_python = _venv_python_path()
    if not venv_python.exists():
        return

    try:
        same_interpreter = Path(sys.executable).resolve() == venv_python.resolve()
    except OSError:
        same_interpreter = False
    if same_interpreter:
        return

    os.execv(
        str(venv_python),
        [str(venv_python), str(__file__), RELAUNCH_FLAG, *sys.argv[1:]],
    )


def main() -> int:
    _relaunch_with_venv_if_available()
    if RELAUNCH_FLAG in sys.argv:
        sys.argv.remove(RELAUNCH_FLAG)

    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

    try:
        from fileclassifier.main import main as app_main
    except ModuleNotFoundError as exc:
        missing = exc.name or "required dependency"
        raise SystemExit(
            f"Cannot start app because '{missing}' is missing. "
            "Run '.\\start.ps1' first to bootstrap dependencies."
        ) from exc

    return app_main()


if __name__ == "__main__":
    raise SystemExit(main())
