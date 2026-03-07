from __future__ import annotations

from fileclassifier.ui.main_window import MainWindow, create_application


def main() -> int:
    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
