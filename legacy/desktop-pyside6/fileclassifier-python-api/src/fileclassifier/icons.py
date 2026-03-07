from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QIcon

from fileclassifier.paths import resource_path


ICON_FILES = {
    "app": "app_icon.svg",
    "dropdown": "dropdown_chevron.svg",
    "choose_excel": "choose_excel.svg",
    "load_sheet": "load_sheet.svg",
    "choose_input": "choose_input.svg",
    "choose_output": "choose_output.svg",
    "apply_filter": "apply_filter.svg",
    "clear_filter": "clear_filter.svg",
    "add_condition": "add_condition.svg",
    "remove_condition": "remove_condition.svg",
    "run": "run.svg",
    "collapse_down": "collapse_down.svg",
    "collapse_right": "collapse_right.svg",
}


@lru_cache(maxsize=None)
def icon_path(name: str) -> Path:
    filename = ICON_FILES[name]
    return resource_path("assets", "icons", filename)


@lru_cache(maxsize=None)
def load_icon(name: str) -> QIcon:
    return QIcon(str(icon_path(name)))
