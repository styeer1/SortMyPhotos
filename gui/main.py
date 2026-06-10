from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.resource_path import resource_path
from gui.window import MainWindow


def main() -> int:
    """Start the SortMyPhotos GUI application."""
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/app_icon.ico")))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())