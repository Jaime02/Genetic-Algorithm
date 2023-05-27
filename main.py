from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from result import Result


def main():
    results = Result.read_all_results()
    app = QApplication()
    app.setStyle("Fusion")
    app.setApplicationName("Genetic Algorithm")
    app.setApplicationDisplayName("Genetic Algorithm")
    app.setWindowIcon(QPixmap("icon.png"))
    window = MainWindow()
    window.add_results(results)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
