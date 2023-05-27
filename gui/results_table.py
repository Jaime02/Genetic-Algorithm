import io
from pathlib import Path

import PIL.Image
from PySide6.QtGui import QStandardItemModel, Qt, QAction, QStandardItem
from PySide6.QtWidgets import QTableView, QAbstractItemView, QMenu, QApplication

from result import Result


categories = [
    "Dataset",
    "Seed",
    "Individual count",
    "Iterations",
    "Crossover probability",
    "Mutation probability",
    "Progenitor selection method",
    "Crossover method",
    "Mutation method",
    "Best fitness",
    "Best individual",
    "Plot",
]

categories_to_index = {category: index for index, category in enumerate(categories)}


class ResultsTableModel(QStandardItemModel):
    def __init__(self):
        QStandardItemModel.__init__(self)
        self.setHorizontalHeaderLabels(categories)


class ResultsTable(QTableView):
    def __init__(self, window: "MainWindow"):
        QTableView.__init__(self)

        self.window = window

        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSortingEnabled(True)

        self.results = []
        self.model = ResultsTableModel()
        self.setModel(self.model)

        self.images: list[io.BytesIO] = []
        self.clicked.connect(self.on_clicked)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def delete_all_results(self):
        # Delete all files inside results/
        for file in Path("results/").glob("*.pickle"):
            file.unlink()

        self.model.removeRows(0, self.model.rowCount())

    def delete_result(self, row: int):
        # Calculate the index of the result in the results list
        values = []
        for column in range(self.model.columnCount()):
            values.append(self.model.item(row, column).text())

        row_hash = Result(*values).calculate_hash()

        # delete results/row_hash.pickle
        Path(f"results/{row_hash}.pickle").unlink()

        self.model.removeRow(row)
        self.images.pop(row)

    def show_context_menu(self, position):
        # Get the index of the selected row
        index = self.indexAt(position)
        row, column = index.row(), index.column()
        menu = QMenu(self)

        copy_text_action = QAction("Copy text", self)
        delete_record_action = QAction("Delete record", self)

        copy_text_action.triggered.connect(
            lambda: QApplication.clipboard().setText(self.model.item(row, column).text())
        )
        delete_record_action.triggered.connect(lambda: self.delete_result(row))

        menu.addAction(copy_text_action)
        menu.addAction(delete_record_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def on_clicked(self, index):
        if index.column() == categories_to_index["Plot"]:
            image_io_buffer = self.images[index.row()]

            image_io_buffer.seek(0)
            loaded_plot: PIL.Image = PIL.Image.open(image_io_buffer, formats=["png"])

            self.window.show_plot(loaded_plot)
            return

    def add_results(self, results: list[Result]):
        for result in results:
            self.add_result(result)

    def add_result(self, result: Result):
        self.images.append(result.plot)
        self.results.append(result)

        row = self.model.rowCount()
        self.model.insertRow(row)

        values = result.to_list()
        for column, value in enumerate(values):
            item = QStandardItem(str(value))
            self.model.setItem(row, column, item)

        plot_item = QStandardItem("Show plot")
        self.model.setItem(row, len(values), plot_item)

        self.resizeColumnsToContents()
