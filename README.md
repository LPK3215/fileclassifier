# FileClassifier Monorepo

This repository contains two active projects:

- `fileclassifier-python-api`: backend API and core matching logic (Python/FastAPI)
- `fileclassifier-react-ui`: web frontend (React/Vite)

Legacy desktop code is archived under `legacy/desktop-pyside6/` and is not part of the active web flow.

## Repository Structure

```text
.
├─ fileclassifier-python-api/
│  ├─ src/fileclassifier/
│  │  ├─ services/
│  │  └─ webapi/
│  │     ├─ app.py
│  │     ├─ schemas.py
│  │     └─ utils/
│  ├─ tests/
│  ├─ DEPLOYMENT.md
│  └─ README.md
├─ fileclassifier-react-ui/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  └─ lib/
│  ├─ DEPLOYMENT.md
│  └─ README.md
├─ scripts/
│  ├─ run_web_backend.ps1
│  ├─ run_web_frontend.ps1
│  ├─ run_desktop_backend.ps1
│  ├─ package_windows_desktop.ps1
│  └─ package_windows_desktop.config.json
├─ start_web.ps1
├─ stop_web.ps1
└─ start_desktop.ps1
```

## Quick Start (Windows)

From repository root:

```powershell
.\start_web.ps1
```

Stop both frontend/backend launched by `start_web.ps1`:

```powershell
.\stop_web.ps1
```

Default endpoints:

- Backend health: `http://127.0.0.1:8000/api/health`
- Frontend UI: `http://127.0.0.1:5173`

## Desktop Mode (Windows)

Single-port desktop style startup (backend + built frontend):

```powershell
.\start_desktop.ps1
```

Default app URL:

- `http://127.0.0.1:18080`

Default data/log paths in desktop runtime:

- Preferred: `<EXE_DIR>\workspace\{excel,input,output,logs}`
- Fallback (if EXE dir is not writable): `%LOCALAPPDATA%\FileClassifier\workspace\{excel,input,output,logs}`
- Each run still creates a condition-named subfolder under `output`.

Desktop config file (optional):

- Path: `fileclassifier.desktop.json` next to the executable.
- Purpose: update port/host/open-browser/runtime-dir without rebuilding.
- Priority: environment variables override config file values.
- Package script now drops both `fileclassifier.desktop.json` and `fileclassifier.desktop.example.json` next to the built executable.

## Build Windows Executable

Build a double-clickable desktop executable (`onefile` by default):

```powershell
.\scripts\package_windows_desktop.ps1
```

Default package UI mode is `console` (a visible terminal window manages the local backend process).

Optional mode:

```powershell
.\scripts\package_windows_desktop.ps1 -Mode onedir
```

Optional UI mode:

```powershell
.\scripts\package_windows_desktop.ps1 -UiMode windowed
```

Single packaging configuration source:

- `scripts/package_windows_desktop.config.json`
- This file contains packaging settings and the generated desktop app config template.
- `scripts/package_windows_desktop.ps1` prints each command before execution so you can see exactly what ran.

Output path:

- `dist-windows\FileClassifierWeb.exe` (`onefile`)
- `dist-windows\FileClassifierWeb\FileClassifierWeb.exe` (`onedir`)

## Project Documentation

- Backend guide: [`fileclassifier-python-api/README.md`](fileclassifier-python-api/README.md)
- Backend deployment: [`fileclassifier-python-api/DEPLOYMENT.md`](fileclassifier-python-api/DEPLOYMENT.md)
- Frontend guide: [`fileclassifier-react-ui/README.md`](fileclassifier-react-ui/README.md)
- Frontend deployment: [`fileclassifier-react-ui/DEPLOYMENT.md`](fileclassifier-react-ui/DEPLOYMENT.md)
- Chinese overview: [`README.zh-CN.md`](README.zh-CN.md)
