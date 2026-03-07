from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fileclassifier.webapi.schemas import DirectoryEntryPayload


def list_directories(directory: Path) -> list[DirectoryEntryPayload]:
    entries: list[DirectoryEntryPayload] = []
    for path in directory.iterdir():
        if path.is_dir():
            entries.append(
                DirectoryEntryPayload(
                    name=path.name or str(path),
                    path=str(path),
                )
            )
    entries.sort(key=lambda item: item.name.casefold())
    return entries


def system_roots() -> list[DirectoryEntryPayload]:
    roots: list[DirectoryEntryPayload] = []
    if os.name == "nt":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:\\")
            if drive.exists():
                roots.append(DirectoryEntryPayload(name=f"{letter}:", path=str(drive)))
    else:
        roots.append(DirectoryEntryPayload(name="/", path="/"))
        home = Path.home()
        if home.exists():
            roots.append(DirectoryEntryPayload(name="~", path=str(home)))
    return roots


def open_directory(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return

    command = ["open", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path)]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Failed to open directory"
        raise RuntimeError(message)


def pick_directory_dialog(initial_dir: Path) -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("System directory picker is unavailable in current runtime.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(
            initialdir=str(initial_dir),
            title="Select Directory",
            mustexist=True,
        )
    finally:
        root.destroy()

    if not selected:
        return None
    return Path(selected)


def pick_excel_file_dialog(initial_dir: Path) -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("System file picker is unavailable in current runtime.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected_file = filedialog.askopenfilename(
            initialdir=str(initial_dir),
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xlsm *.xltx *.xltm")],
        )
    finally:
        root.destroy()

    if not selected_file:
        return None
    return Path(selected_file)


def pick_excel_source_dialog(initial_dir: Path) -> tuple[Path | None, str]:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("System file picker is unavailable in current runtime.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        # Yes => file, No => directory, Cancel => canceled.
        choice = messagebox.askyesnocancel(
            title="选择 Excel 来源",
            message="选择“是”打开单个 Excel 文件，选择“否”打开文件夹。",
            icon="question",
        )
        if choice is None:
            return None, "none"

        if choice:
            selected_file = filedialog.askopenfilename(
                initialdir=str(initial_dir),
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xlsm *.xltx *.xltm")],
            )
            if not selected_file:
                return None, "none"
            return Path(selected_file), "file"

        selected_dir = filedialog.askdirectory(
            initialdir=str(initial_dir),
            title="Select Excel Directory",
            mustexist=True,
        )
        if not selected_dir:
            return None, "none"
        return Path(selected_dir), "directory"
    finally:
        root.destroy()
