# FileClassifier Frontend Deployment Guide

Native-command deployment for the React UI.

## 1. Prerequisites

- Node.js 18+
- npm
- Backend API available (default: `http://127.0.0.1:8000`)

## 2. Enter Frontend Directory

```powershell
cd fileclassifier-react-ui
```

## 3. Install Dependencies

```powershell
npm install
```

In CI environments, prefer:

```powershell
npm ci
```

## 4. Configure API Base (Optional)

Create `.env.production` for production deployment:

```dotenv
VITE_API_BASE=http://127.0.0.1:8000/api
```

If frontend and backend are reverse-proxied under the same domain with `/api`,
you can keep the default `/api`.

## 5. Development Run

```powershell
npm run dev
```

Default dev URL: `http://127.0.0.1:5173`

## 6. Build Production Assets

```powershell
npm run build
```

Output: `dist/`

## 7. Local Preview for Built Assets

```powershell
npm run preview -- --host 0.0.0.0 --port 5173
```

## 8. Serve Built Assets

Example:

```powershell
npx --yes serve dist -l 5173
```

Then open `http://127.0.0.1:5173`.

