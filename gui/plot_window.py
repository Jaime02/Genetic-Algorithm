import PIL.Image
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QLabel


class PlotWindow(QMainWindow):
    def __init__(self, window: "MainWindow", plot: PIL.Image):
        QMainWindow.__init__(self, window)

        self.setWindowTitle("Best fitnesses plot")

        self.central_widget = QLabel()
        self.central_widget.setPixmap(QPixmap.fromImage(ImageQt(plot)))

        self.setCentralWidget(self.central_widget)
