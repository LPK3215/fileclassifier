# FileClassifier React UI

Web frontend for the FileClassifier workflow.

## Features

- Load Excel by file or folder (folder mode auto lists files)
- Auto-read sheet metadata and preview
- Query conditions with AND/OR and range modal
- Right preview table with:
  - column pinning
  - column resize
  - sorting
  - column filters
- Execute copy workflow and inspect result log

## Tech Stack

- React 18
- Vite 5

## Current Frontend Structure

```text
fileclassifier-react-ui/
├─ src/
│  ├─ components/                 # UI cards and reusable controls
│  ├─ hooks/                      # stateful logic (conditions/table/splitter)
│  ├─ lib/                        # api client and shared helpers
│  ├─ App.jsx                     # page composition / orchestration
│  ├─ main.jsx
│  └─ styles.css
├─ package.json
└─ vite.config.js
```

## Install

```powershell
npm install
```

## Run Dev Server

```powershell
npm run dev
```

Default URL: `http://127.0.0.1:5173`

Dev proxy in `vite.config.js`:

- `/api` -> `http://127.0.0.1:8000`

## Build

```powershell
npm run build
```

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md).

