import io
from pathlib import Path

import PIL.Image
from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, Qt, QAction, QStandardItem
from PySide6.QtWidgets import QTableView, QAbstractItemView, QMenu, QApplication

from genetic_algorithm.genetic_functions import NamedFunction
from genetic_algorithm.result import Result

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

        self.results = []
        self.images: list[io.BytesIO] = []
        self.add_results(Result.read_all_results())

    def add_results(self, results: list[Result]):
        for result in results:
            self.add_result(result)

    def delete_all_results(self):
        # Delete all files inside results/
        for file in Path("results/").glob("*.pickle"):
            file.unlink()

        self.removeRows(0, self.rowCount())

    def add_result(self, result: Result):
        self.images.append(result.plot)
        self.results.append(result)

        new_row = self.rowCount()
        self.insertRow(new_row)

        values = result.to_list()
        for column, value in enumerate(values):
            item = QStandardItem()
            item.setText(str(value))
            item.setData(value, Qt.UserRole)
            self.setItem(new_row, column, item)

        plot_item = QStandardItem("Show plot")
        self.setItem(new_row, len(values), plot_item)

    def removeRow(self, row: int, parent=...) -> bool:
        # Calculate the index of the result in the results list
        values = []
        for column in range(self.columnCount()):
            values.append(self.item(row, column).text())

        row_hash = Result(*values).calculate_hash()

        # delete results/row_hash.pickle
        Path(f"results/{row_hash}.pickle").unlink()

        self.results.pop(row)
        self.images.pop(row)
        return QStandardItemModel.removeRow(self, row, parent)


class SortModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left = self.sourceModel().data(left, Qt.UserRole)
        right = self.sourceModel().data(right, Qt.UserRole)
        if isinstance(left, NamedFunction):
            return left.name < right.name
        return bool(left < right)


class ResultsTable(QTableView):
    def __init__(self, window: "MainWindow"):
        QTableView.__init__(self)
        self.window = window

        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSortingEnabled(True)

        self.main_model = ResultsTableModel()
        self.sort_model = SortModel()
        self.sort_model.setSourceModel(self.main_model)
        self.setModel(self.sort_model)

        self.clicked.connect(self.on_clicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.resizeColumnsToContents()

    def rowsInserted(self, parent, start: int, end: int):
        QTableView.rowsInserted(self, parent, start, end)
        self.resizeColumnsToContents()

    def show_context_menu(self, position):
        # Get the index of the selected row
        index = self.indexAt(position)
        row, column = index.row(), index.column()
        menu = QMenu(self)

        copy_text_action = QAction("Copy text", self)
        delete_record_action = QAction("Delete record", self)

        copy_text_action.triggered.connect(
            lambda: QApplication.clipboard().setText(self.main_model.item(row, column).text())
        )
        delete_record_action.triggered.connect(lambda: self.main_model.removeRow(row))

        menu.addAction(copy_text_action)
        menu.addAction(delete_record_action)

        menu.exec(self.viewport().mapToGlobal(position))

    def on_clicked(self, index):
        if index.column() != categories_to_index["Plot"]:
            return

        image_io_buffer = self.main_model.images[index.row()]
        image_io_buffer.seek(0)
        loaded_plot: PIL.Image = PIL.Image.open(image_io_buffer, formats=["png"])

        self.window.show_plot(loaded_plot)
