from pathlib import Path

import qdarktheme
from PySide6.QtCore import QLocale
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from genetic_algorithm.result import Result


def main():
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))

    app = QApplication()
    app.setApplicationName("Genetic Algorithm")
    app.setApplicationDisplayName("Genetic Algorithm")
    app.setWindowIcon(QPixmap("icon.png"))
    qdarktheme.setup_theme(additional_qss=Path("stylesheet.qss").read_text())

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
