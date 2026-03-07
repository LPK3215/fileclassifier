# FileClassifier Python API

Backend service for Excel-driven query filtering and file copy workflow.

## Tech Stack

- Python 3.10+
- FastAPI + Uvicorn
- pandas + openpyxl
- pytest + ruff

## Current Backend Structure

```text
fileclassifier-python-api/
├─ src/fileclassifier/
│  ├─ services/                    # domain logic (workflow/query/matcher/excel)
│  └─ webapi/
│     ├─ app.py                    # API route assembly
│     ├─ schemas.py                # request/response models
│     └─ utils/
│        ├─ pathing.py             # path resolve + excel file listing
│        ├─ system_io.py           # OS dialogs / folder open / roots listing
│        └─ serialization.py       # payload conversion helpers
├─ tests/
├─ DEPLOYMENT.md
├─ start_web.py
└─ start_desktop.py
```

## Key API Endpoints

- `GET /api/health`
- `GET /api/excel/files`
- `POST /api/excel/metadata`
- `POST /api/excel/preview`
- `POST /api/query/filter-preview`
- `POST /api/workflow/execute`
- `POST /api/system/pick-excel-file` (Excel file picker)
- `POST /api/system/pick-excel-source` (file/folder unified picker)
- `POST /api/system/pick-directory`
- `POST /api/system/open-folder`

## Run Locally (Windows)

```powershell
python .\start_web.py
```

Startup parameters are preset in `start_web.py` (`APP_HOST`, `APP_PORT`, `APP_RELOAD`, `APP_WORKERS`).

Default health URL:

- `http://127.0.0.1:8000/api/health`

Desktop single-port mode:

```powershell
python .\start_desktop.py
```

Desktop URL:

- `http://127.0.0.1:18080`

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests scripts start_web.py start_desktop.py
```

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for native command deployment steps.
