# FileClassifier Backend Deployment Guide

Native-command deployment (no wrapper script required).

## 1. Prerequisites

- Python 3.10+
- Network access for package installation

## 2. Enter Project Directory

```powershell
cd fileclassifier-python-api
```

## 3. Create Virtual Environment

Windows:

```powershell
python -m venv .venv
```

Linux/macOS:

```bash
python3 -m venv .venv
```

## 4. Install Dependencies

Runtime only:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[web]"
```

Runtime + test/lint tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web,dev]"
```

## 5. Start Backend

```powershell
python .\start_web.py
```

`start_web.py` contains preset startup values:

- `APP_HOST`
- `APP_PORT`
- `APP_RELOAD`
- `APP_WORKERS`

## 5.1 Start Desktop Mode (Single Port)

Desktop mode serves built frontend assets and API from one process.

```powershell
python .\start_desktop.py
```

Default desktop URL:

- `http://127.0.0.1:18080`

If you need a different port:

```powershell
$env:FILECLASSIFIER_PORT = "28080"
python .\start_desktop.py
```

You can also place `fileclassifier.desktop.json` next to `start_desktop.py` (or next to packaged EXE) and define:

```json
{
  "host": "127.0.0.1",
  "port": 18080,
  "open_browser": true,
  "runtime_dir": "workspace",
  "reload": false,
  "workers": 1
}
```

Environment variables still take precedence over this file.

## 6. Verify API

```powershell
curl http://127.0.0.1:8000/api/health
```

Expected:

```json
{"status":"ok"}
```

## 7. Optional Quality Checks

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests scripts start_web.py
```

## 8. Build Windows Executable (from repo root)

```powershell
.\scripts\package_windows_desktop.ps1
```

Or:

```powershell
.\scripts\package_windows_desktop.ps1 -Mode onedir
```

Packaging settings are centralized in:

- `scripts/package_windows_desktop.config.json`

The packaging script prints each executed command for easier review.
