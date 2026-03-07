# Contributing to FileClassifier

Thanks for contributing.

## Ground Rules

- Be respectful and constructive.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- Keep pull requests focused and small when possible.

## Local Setup

### Fast path (Windows)

```powershell
.\start_web.ps1
```

### Manual path

```powershell
python -m venv fileclassifier-python-api/.venv
.\fileclassifier-python-api\.venv\Scripts\python.exe -m pip install --upgrade pip
.\fileclassifier-python-api\.venv\Scripts\python.exe -m pip install -e "fileclassifier-python-api[dev]"
```

## Run Checks

```powershell
.\fileclassifier-python-api\.venv\Scripts\python.exe -m ruff check fileclassifier-python-api/src fileclassifier-python-api/tests fileclassifier-python-api/scripts fileclassifier-python-api/start_web.py
.\fileclassifier-python-api\.venv\Scripts\python.exe -m pytest fileclassifier-python-api/tests
```

## Pull Request Checklist

- Add or update tests for behavior changes.
- Keep docs in sync when commands/workflows change.
- Ensure lint and tests pass locally.
- Describe user-facing impact in the PR.

## Commit Style

Any clear style is accepted. If possible, use concise commits with one logical change each.
