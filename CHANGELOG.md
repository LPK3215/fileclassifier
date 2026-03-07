# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Frontend architecture split:
  - `src/components/*` for page cards and controls
  - `src/hooks/*` for conditions/table/splitter state logic
  - `src/lib/*` for API and shared helpers
- Backend webapi utility split:
  - `src/fileclassifier/webapi/utils/pathing.py`
  - `src/fileclassifier/webapi/utils/system_io.py`
  - `src/fileclassifier/webapi/utils/serialization.py`
- Unified picker endpoint:
  - `POST /api/system/pick-excel-source` (file/folder source selection)
- Open-source community baseline files for GitHub:
  - `LICENSE`
  - `README.md`
  - `CONTRIBUTING.md`
  - `CODE_OF_CONDUCT.md`
  - `SECURITY.md`
  - `SUPPORT.md`
  - `.github` issue/PR templates and CI workflow
  - `.gitignore`
- Packaging improvements:
  - robust Windows packaging script (`legacy/desktop-pyside6/fileclassifier-python-api/scripts/package_windows.ps1`) with mode switch and
    PyInstaller install fallback mirror
  - Linux packaging script (`legacy/desktop-pyside6/fileclassifier-python-api/scripts/package_linux.sh`)
  - multi-platform binary workflow (`legacy/desktop-pyside6/.github/workflows/build-binaries.yml`) for
    Windows/Linux onedir/onefile artifacts
- Windows desktop web packaging/runtime:
  - single-port desktop entrypoint `fileclassifier-python-api/start_desktop.py` (auto-opens browser)
  - Windows packaging script `scripts/package_windows_desktop.ps1` for onefile/onedir executable output
  - desktop startup scripts `start_desktop.ps1` and `scripts/run_desktop_backend.ps1`
  - backend static frontend serving support in `fileclassifier-python-api/src/fileclassifier/webapi/app.py`
- Runtime default-path API and policy:
  - `GET /api/system/default-paths` endpoint
  - runtime-aware defaults for desktop/development (`workspace` vs `data`)
  - desktop runtime path fallback to `%LOCALAPPDATA%\FileClassifier\workspace` when app directory is not writable
- Desktop runtime config file support:
  - optional `fileclassifier.desktop.json` loaded next to EXE (or project in source mode)
  - overridable fields: `host`, `port`, `open_browser`, `runtime_dir`, `reload`, `workers`
  - `FILECLASSIFIER_CONFIG` for explicit config path
- One-command web stack stop script:
  - root `stop_web.ps1` reads tracked PIDs from `.runtime\web-stack\processes.json`
- Single-source packaging config:
  - `scripts/package_windows_desktop.config.json` now holds packaging settings and desktop config template
  - packaging script prints executed commands for full auditability
- Execution output improvements:
  - each run writes results into condition-named subfolder under output directory
  - run logs are persisted per run (`run_summary.txt`, `run_report.json`, `record_matches.csv`)

### Changed

- Frontend `App.jsx` moved to orchestration role after module split.
- Backend `webapi/app.py` simplified by extracting reusable helper logic.
- Root/backend/frontend READMEs and deployment guides updated to current structure.
- Desktop packaging default UI mode changed to `console` (persistent visible terminal window).
- `start_web.ps1` now records launched frontend/backend shell PIDs for deterministic shutdown via `stop_web.ps1`.
- Packaging spec output moved under `scripts` (`--specpath scripts`) to keep packaging artifacts centralized.
- Frontend default directory autofill removed for Step 3:
  - input/output paths start empty
  - execution requires explicit input/output directory selection

### Fixed

- PowerShell packaging script value-casting bug (`[string]$obj.prop`) that could build malformed entry-script paths.
- Desktop launcher console auto-close behavior on startup failure/port conflicts:
  - now prompts and waits for user acknowledgement before closing.

## [1.0.0] - 2026-03-07

### Added

- Initial desktop release with Excel query filtering, file matching, copy workflow,
  and GUI viewer.
