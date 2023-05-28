from pathlib import Path

import qdarktheme
from PySide6.QtCore import QLocale
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))

    app = QApplication()
    app.setApplicationName("Genetic Algorithm")
    app.setApplicationDisplayName("Genetic Algorithm")
    app.setWindowIcon(QPixmap("icon.png"))
    stylesheet = (Path("gui") / "stylesheet.qss").read_text()
    qdarktheme.setup_theme(additional_qss=stylesheet)

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
