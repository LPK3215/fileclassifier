from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
RELAUNCH_FLAG = "--__fileclassifier_relaunched"

# Preset startup configuration: start by running this file directly.
APP_IMPORT = "fileclassifier.webapi.app:create_app"
APP_FACTORY = True
APP_HOST = "127.0.0.1"
APP_PORT = 8000
APP_RELOAD = False
APP_WORKERS = 1


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
        import uvicorn
    except ModuleNotFoundError as exc:
        missing = exc.name or "required dependency"
        raise SystemExit(
            f"Cannot start web API because '{missing}' is missing. "
            "Install with '.\\.venv\\Scripts\\python.exe -m pip install -e \".[web]\"'."
        ) from exc

    if APP_RELOAD and APP_WORKERS > 1:
        raise SystemExit("APP_RELOAD cannot be true when APP_WORKERS is greater than 1.")

    uvicorn.run(
        APP_IMPORT,
        factory=APP_FACTORY,
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
        workers=APP_WORKERS,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
