from __future__ import annotations

import json
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
RELAUNCH_FLAG = "--__fileclassifier_relaunched"
APP_NAME = "FileClassifier"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18080
DEFAULT_RELOAD = False
DEFAULT_WORKERS = 1
DEFAULT_OPEN_BROWSER = True
CONFIG_FILENAME = "fileclassifier.desktop.json"


@dataclass(slots=True)
class DesktopSettings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    reload: bool = DEFAULT_RELOAD
    workers: int = DEFAULT_WORKERS
    open_browser: bool = DEFAULT_OPEN_BROWSER
    runtime_dir: Path | None = None
    config_path: Path | None = None


def _parse_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{field_name} must be a boolean value")


def _parse_port(value: Any, field_name: str) -> int:
    port = int(str(value).strip())
    if port < 1 or port > 65535:
        raise ValueError(f"{field_name} must be in range 1-65535")
    return port


def _parse_workers(value: Any, field_name: str) -> int:
    workers = int(str(value).strip())
    if workers < 1:
        raise ValueError(f"{field_name} must be >= 1")
    return workers


def _config_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        try:
            executable = executable.resolve()
        except OSError:
            pass
        return executable.parent
    return PROJECT_ROOT


def _read_json_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON object")
    return data


def _resolve_config_path() -> Path | None:
    env_path = os.getenv("FILECLASSIFIER_CONFIG", "").strip()
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.exists():
            return candidate
        raise ValueError(f"Configured FILECLASSIFIER_CONFIG does not exist: {candidate}")

    default_path = _config_base_dir() / CONFIG_FILENAME
    if default_path.exists():
        return default_path
    return None


def _resolve_configured_runtime_dir(raw_value: Any, config_path: Path | None) -> Path | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    candidate = Path(text).expanduser()
    if not candidate.is_absolute() and config_path is not None:
        candidate = config_path.parent / candidate
    return candidate


def _load_desktop_settings() -> DesktopSettings:
    settings = DesktopSettings()

    config_path = _resolve_config_path()
    config_data: dict[str, Any] = {}
    if config_path is not None:
        config_data = _read_json_config(config_path)
        settings.config_path = config_path

    if "host" in config_data:
        host = str(config_data.get("host", "")).strip()
        if host:
            settings.host = host
    if "port" in config_data:
        settings.port = _parse_port(config_data["port"], "config.port")
    if "reload" in config_data:
        settings.reload = _parse_bool(config_data["reload"], "config.reload")
    if "workers" in config_data:
        settings.workers = _parse_workers(config_data["workers"], "config.workers")
    if "open_browser" in config_data:
        settings.open_browser = _parse_bool(config_data["open_browser"], "config.open_browser")
    if "runtime_dir" in config_data:
        settings.runtime_dir = _resolve_configured_runtime_dir(config_data["runtime_dir"], config_path)

    env_host = os.getenv("FILECLASSIFIER_HOST", "").strip()
    if env_host:
        settings.host = env_host

    env_port = os.getenv("FILECLASSIFIER_PORT", "").strip()
    if env_port:
        settings.port = _parse_port(env_port, "FILECLASSIFIER_PORT")

    env_reload = os.getenv("FILECLASSIFIER_RELOAD", "").strip()
    if env_reload:
        settings.reload = _parse_bool(env_reload, "FILECLASSIFIER_RELOAD")

    env_workers = os.getenv("FILECLASSIFIER_WORKERS", "").strip()
    if env_workers:
        settings.workers = _parse_workers(env_workers, "FILECLASSIFIER_WORKERS")

    env_open_browser = os.getenv("FILECLASSIFIER_OPEN_BROWSER", "").strip()
    if env_open_browser:
        settings.open_browser = _parse_bool(env_open_browser, "FILECLASSIFIER_OPEN_BROWSER")

    env_runtime_dir = os.getenv("FILECLASSIFIER_RUNTIME_DIR", "").strip()
    if env_runtime_dir:
        settings.runtime_dir = Path(env_runtime_dir).expanduser()

    return settings


def _fallback_runtime_root() -> Path:
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA", "").strip()
        if base:
            return Path(base) / APP_NAME / "workspace"
    return Path.home() / f".{APP_NAME.lower()}" / "workspace"


def _ensure_writable_dir(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def _resolve_runtime_root(runtime_dir_hint: Path | None = None) -> Path:
    if runtime_dir_hint is not None and _ensure_writable_dir(runtime_dir_hint):
        return runtime_dir_hint

    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable)
        try:
            executable_dir = executable_dir.resolve()
        except OSError:
            pass
        preferred = executable_dir.parent / "workspace"
    else:
        preferred = PROJECT_ROOT / ".runtime" / "workspace"

    if _ensure_writable_dir(preferred):
        return preferred

    fallback = _fallback_runtime_root()
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _setup_logging(runtime_root: Path, include_console: bool) -> Path:
    log_dir = runtime_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "desktop.log"

    handlers: list[logging.Handler] = [logging.FileHandler(log_path, encoding="utf-8")]
    if include_console:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )
    return log_path


def _log_runtime_banner(
    app_url: str,
    runtime_root: Path,
    log_path: Path,
    settings: DesktopSettings,
) -> None:
    logging.info("Desktop service URL: %s", app_url)
    logging.info("Desktop bind host/port: %s:%s", settings.host, settings.port)
    logging.info("Browser auto-open: %s", settings.open_browser)
    if settings.config_path is not None:
        logging.info("Loaded config file: %s", settings.config_path)
    else:
        logging.info("Config file not found, using defaults/environment variables.")
    logging.info("Runtime workspace: %s", runtime_root)
    logging.info("Desktop log file: %s", log_path)
    logging.info("Close this window to stop the local service.")


def _pause_before_exit(has_console: bool, message: str) -> None:
    if not has_console:
        return
    try:
        print(message)
        input()
    except EOFError:
        return


def _show_message_box(title: str, message: str) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        pass


def _has_console_streams() -> bool:
    return getattr(sys, "stdout", None) is not None and getattr(sys, "stderr", None) is not None


def _venv_python_path() -> Path:
    if os.name == "nt":
        return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".venv" / "bin" / "python"


def _relaunch_with_venv_if_available() -> None:
    if RELAUNCH_FLAG in sys.argv:
        return

    venv_python = _venv_python_path()
    if not venv_python.exists():
        return

    try:
        same_interpreter = Path(sys.executable).resolve() == venv_python.resolve()
    except OSError:
        same_interpreter = False

    if same_interpreter:
        return

    os.execv(
        str(venv_python),
        [str(venv_python), str(__file__), RELAUNCH_FLAG, *sys.argv[1:]],
    )


def _wait_and_open_browser(host: str, port: int, timeout_seconds: int = 30) -> None:
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{connect_host}:{port}"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with socket.create_connection((connect_host, port), timeout=0.5):
                _open_url(url)
                logging.info("Opened browser at %s", url)
                return
        except OSError:
            time.sleep(0.25)
    logging.warning("Timed out waiting to open browser at %s", url)


def _open_url(url: str) -> None:
    if os.name == "nt":
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return
        except Exception:
            logging.exception("os.startfile failed for %s", url)
    webbrowser.open(url, new=1)


def _is_server_alive(host: str, port: int, timeout_seconds: float = 0.5) -> bool:
    connect_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    try:
        with socket.create_connection((connect_host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _healthcheck(url: str) -> bool:
    try:
        with urlopen(url, timeout=1.0) as response:
            return response.status == 200
    except URLError:
        return False
    except Exception:
        return False


def main() -> int:
    try:
        settings = _load_desktop_settings()
    except Exception as exc:
        message = (
            "Desktop configuration is invalid.\n"
            f"Error: {exc}\n\n"
            f"Please check {CONFIG_FILENAME} (or FILECLASSIFIER_CONFIG)."
        )
        print(message, file=sys.stderr)
        _show_message_box("FileClassifier 配置错误", message)
        return 1

    os.environ.setdefault("FILECLASSIFIER_DESKTOP_MODE", "1")
    runtime_root = _resolve_runtime_root(settings.runtime_dir)
    os.environ["FILECLASSIFIER_RUNTIME_DIR"] = str(runtime_root)

    has_console = _has_console_streams()
    log_path = _setup_logging(runtime_root, include_console=has_console)
    logging.info("Desktop launcher started. executable=%s", sys.executable)

    _relaunch_with_venv_if_available()
    if RELAUNCH_FLAG in sys.argv:
        sys.argv.remove(RELAUNCH_FLAG)

    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        missing = exc.name or "required dependency"
        raise SystemExit(
            f"Cannot start desktop mode because '{missing}' is missing. "
            "Install with '.\\.venv\\Scripts\\python.exe -m pip install -e \".[web]\"'."
        ) from exc

    try:
        from fileclassifier.webapi.app import create_app
    except ModuleNotFoundError as exc:
        missing = exc.name or "fileclassifier"
        raise SystemExit(
            f"Cannot start desktop mode because '{missing}' is missing in runtime package."
        ) from exc

    if settings.reload and settings.workers > 1:
        raise SystemExit("reload cannot be true when workers is greater than 1.")

    app_url = f"http://127.0.0.1:{settings.port}"
    health_url = f"{app_url}/api/health"
    _log_runtime_banner(app_url, runtime_root, log_path, settings)

    if _is_server_alive(settings.host, settings.port):
        logging.info("Port %s already in use. health_ok=%s", settings.port, _healthcheck(health_url))
        try:
            _open_url(app_url)
        except Exception:
            logging.exception("Failed to open URL when server already alive: %s", app_url)
        _pause_before_exit(
            has_console,
            (
                f"Port {settings.port} is already in use. "
                "The service may already be running in another window.\n"
                "Press Enter to close this window..."
            ),
        )
        return 0

    if settings.open_browser:
        threading.Thread(
            target=_wait_and_open_browser,
            args=(settings.host, settings.port),
            daemon=True,
        ).start()

    try:
        uvicorn.run(
            create_app(),
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            workers=settings.workers,
            log_config=None,
            access_log=has_console,
        )
    except Exception as exc:
        logging.exception("Desktop server crashed")
        _show_message_box(
            "FileClassifier 启动失败",
            f"程序启动失败：{exc}\n\n日志文件：{log_path}\n\n请把日志发给开发者。",
        )
        _pause_before_exit(has_console, "Startup failed. Press Enter to close this window...")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
