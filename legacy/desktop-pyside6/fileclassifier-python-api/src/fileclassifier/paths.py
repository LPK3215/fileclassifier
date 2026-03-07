from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parent


def resource_path(*parts: str) -> Path:
    return app_root().joinpath(*parts)
