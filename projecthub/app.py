"""QApplication bootstrap."""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .config import APP_NAME, ICON_FILE
from .main_window import ProjectHub


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("ProjectHub")

    if ICON_FILE.exists():
        app.setWindowIcon(QIcon(str(ICON_FILE)))

    app.setStyle("Fusion")

    window = ProjectHub()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
