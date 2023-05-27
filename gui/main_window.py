import json
from copy import deepcopy
from dataclasses import dataclass
from itertools import product

import PIL.Image
from PySide6.QtCore import QSettings, Slot, QObject, Signal, QThread, QPoint
from PySide6.QtGui import Qt, QIntValidator, QDoubleValidator, QShowEvent, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QHBoxLayout,
    QDockWidget,
    QSizePolicy,
    QBoxLayout,
    QCheckBox,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QProgressDialog, QMessageBox,
)

from experiment import run_experiment
from genetic_functions import ProgenitorSelectionFunction, MutationFunction, CrossoverFunction, NamedFunction
from gui.plot_window import PlotWindow
from gui.results_table import ResultsTable, categories, categories_to_index
from result import Result


@dataclass
class ExperimentSettings:
    experiment_count: int
    seed: int
    dataset_filename: str
    progenitor_selection_function: NamedFunction
    mutation_function: NamedFunction
    crossover_function: NamedFunction
    initial_individual_count: int
    individual_count_increase: int
    initial_iterations: int
    iterations_increase: int
    initial_crossover_probability: float
    crossover_probability_increase: float
    initial_mutation_probability: float
    mutation_probability_increase: float


class ExperimentRunner(QObject):
    finished = Signal()
    result_ready = Signal(int, Result)

    def __init__(self, experiment_settings: list[ExperimentSettings]):
        super().__init__()
        self.experiment_settings = experiment_settings

    def run(self):
        for settings_number, settings in enumerate(self.experiment_settings):
            experiment_count = settings.experiment_count
            seed = settings.seed
            dataset_filename = settings.dataset_filename
            progenitor_selection_function = settings.progenitor_selection_function
            mutation_function = settings.mutation_function
            crossover_function = settings.crossover_function
            initial_individual_count = settings.initial_individual_count
            individual_count_increase = settings.individual_count_increase
            initial_iterations = settings.initial_iterations
            iterations_increase = settings.iterations_increase
            initial_crossover_probability = settings.initial_crossover_probability
            crossover_probability_increase = settings.crossover_probability_increase
            initial_mutation_probability = settings.initial_mutation_probability
            mutation_probability_increase = settings.mutation_probability_increase

            for i in range(experiment_count):
                if QThread.currentThread().isInterruptionRequested():
                    self.finished.emit()
                    break

                individual_count = max(2, initial_individual_count + i * individual_count_increase)
                iterations = max(1, initial_iterations + i * iterations_increase)

                crossover_probability = initial_crossover_probability + i * crossover_probability_increase
                crossover_probability = max(0, min(1, crossover_probability))
                mutation_probability = initial_mutation_probability + i * mutation_probability_increase
                mutation_probability = max(0, min(1, mutation_probability))

                result = run_experiment(
                    dataset_filename=dataset_filename,
                    seed=seed,
                    individual_count=individual_count,
                    iterations=iterations,
                    progenitor_selection_function=progenitor_selection_function,
                    mutation_function=mutation_function,
                    crossover_function=crossover_function,
                    crossover_probability=crossover_probability,
                    mutation_probability=mutation_probability,
                )
                result.save()

                experiment_number = settings_number * experiment_count + i
                self.result_ready.emit(experiment_number, result)

        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Genetic Algorithm experiments")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.central_layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        self.setDockOptions(QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)

        self.filters_dock = QDockWidget("Filters", self)
        self.filters_dock.setObjectName("filters_dock")
        self.filters_dock.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.filters_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.filters_dock)

        self.filters_widget = QWidget()
        self.filters_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.filters_dock.setWidget(self.filters_widget)

        self.filters_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.filters_widget.setLayout(self.filters_layout)

        def change_filter_layout_orientation():
            if self.dockWidgetArea(self.filters_dock) in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea, Qt.NoDockWidgetArea):
                self.filters_layout.setDirection(QBoxLayout.TopToBottom)
                return

            if self.dockWidgetArea(self.filters_dock) in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                self.filters_layout.setDirection(QBoxLayout.LeftToRight)
                return

        self.filters_dock.dockLocationChanged.connect(change_filter_layout_orientation)

        self.filters_checkboxes = []
        for category in categories:
            checkbox = QCheckBox(category)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, c=checkbox: self.filter_changed(c))
            self.filters_layout.addWidget(checkbox)
            self.filters_checkboxes.append(checkbox)

        self.filters_layout.addStretch()

        self.results_table = ResultsTable(self)
        self.central_layout.addWidget(self.results_table)

        self.experiment_settings_dock = QDockWidget("Experiment settings", self)
        self.experiment_settings_dock.setObjectName("experiment_settings_dock")
        self.experiment_settings_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.experiment_settings_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.experiment_settings_dock)

        self.experiment_settings_widget = QWidget()
        self.experiment_settings_dock.setWidget(self.experiment_settings_widget)

        self.experiment_settings_layout = QVBoxLayout()
        self.experiment_settings_widget.setLayout(self.experiment_settings_layout)

        self.settings_layout = QFormLayout()
        self.experiment_settings_layout.addLayout(self.settings_layout)

        self.dataset_label = QLabel("Dataset:")
        self.dataset_combobox = QComboBox()
        self.dataset_combobox.addItems(
            [
                "Diabetes",
                "Quake",
                "Laser",
            ]
        )
        self.dataset_combobox.setCurrentIndex(0)
        self.settings_layout.addRow(self.dataset_label, self.dataset_combobox)

        self.experiment_count_label = QLabel("Experiment count:")
        self.experiment_count_input = QLineEdit("5")
        self.experiment_count_input.setValidator(QIntValidator())
        self.experiment_count_input.setMaxLength(3)
        self.settings_layout.addRow(self.experiment_count_label, self.experiment_count_input)

        self.seed_label = QLabel("Experiment seed:")
        self.seed_input = QLineEdit("33")
        self.seed_input.setValidator(QIntValidator())
        self.seed_input.setMaxLength(10)
        self.settings_layout.addRow(self.seed_label, self.seed_input)

        self.mutation_function_label = QLabel("Mutation function:")
        self.mutation_function_combobox = QComboBox()
        self.mutation_function_combobox.addItems(
            [
                "Uniform",
                "Non-uniform",
            ]
        )
        self.mutation_function_combobox.setCurrentIndex(0)
        self.settings_layout.addRow(self.mutation_function_label, self.mutation_function_combobox)

        self.crossover_function_label = QLabel("Crossover function:")
        self.crossover_function_combobox = QComboBox()
        self.crossover_function_combobox.addItems(
            [
                "Single point",
                "Two points",
            ]
        )

        self.crossover_function_combobox.setCurrentIndex(0)
        self.settings_layout.addRow(self.crossover_function_label, self.crossover_function_combobox)

        self.progenitor_selection_function = QLabel("Progenitor selection:")
        self.progenitor_selection_function_combobox = QComboBox()
        self.progenitor_selection_function_combobox.addItems(
            [
                "Roulette",
                "Tournament with replacement",
                "Tournament without replacement",
            ]
        )
        self.progenitor_selection_function_combobox.setCurrentIndex(0)
        self.settings_layout.addRow(self.progenitor_selection_function, self.progenitor_selection_function_combobox)

        self.values_layout = QHBoxLayout()
        self.experiment_settings_layout.addLayout(self.values_layout)

        self.initial_value_layout = QFormLayout()
        self.values_layout.addLayout(self.initial_value_layout)

        self.increase_value_layout = QFormLayout()
        self.values_layout.addLayout(self.increase_value_layout)

        self.individual_count_label = QLabel("Individual count:")
        self.individual_count_input = QLineEdit("100")
        self.individual_count_input.setValidator(QIntValidator())
        self.individual_count_input.setMaxLength(3)
        self.initial_value_layout.addRow(self.individual_count_label, self.individual_count_input)

        self.individual_count_increase_label = QLabel("Increase by:")
        self.individual_count_increase_input = QLineEdit("20")
        self.individual_count_increase_input.setValidator(QIntValidator())
        self.individual_count_increase_input.setMaxLength(3)
        self.increase_value_layout.addRow(self.individual_count_increase_label, self.individual_count_increase_input)

        self.iterations_label = QLabel("Iterations:")
        self.iterations_input = QLineEdit("100")
        self.iterations_input.setValidator(QIntValidator())
        self.iterations_input.setMaxLength(3)
        self.initial_value_layout.addRow(self.iterations_label, self.iterations_input)

        self.iterations_increase_label = QLabel("Increase by:")
        self.iterations_increase_input = QLineEdit("100")
        self.iterations_increase_input.setValidator(QIntValidator())
        self.iterations_increase_input.setMaxLength(3)
        self.increase_value_layout.addRow(self.iterations_increase_label, self.iterations_increase_input)

        self.positive_double_validator = QDoubleValidator()
        self.positive_double_validator.setTop(1.0)
        self.positive_double_validator.setBottom(0.0)
        self.positive_double_validator.setDecimals(4)
        self.positive_double_validator.setNotation(QDoubleValidator.StandardNotation)

        self.negative_double_validator = QDoubleValidator()
        self.negative_double_validator.setTop(1.0)
        self.negative_double_validator.setBottom(-1.0)
        self.negative_double_validator.setDecimals(4)
        self.negative_double_validator.setNotation(QDoubleValidator.StandardNotation)

        self.crossover_probability_label = QLabel("Crossover probability:")
        self.crossover_probability_input = QLineEdit("0.8")
        self.crossover_probability_input.setValidator(self.positive_double_validator)
        self.initial_value_layout.addRow(self.crossover_probability_label, self.crossover_probability_input)

        self.crossover_probability_increase_label = QLabel("Increase by:")
        self.crossover_probability_increase_input = QLineEdit("-0.05")
        self.crossover_probability_increase_input.setValidator(self.negative_double_validator)
        self.increase_value_layout.addRow(
            self.crossover_probability_increase_label, self.crossover_probability_increase_input
        )

        self.mutation_probability_label = QLabel("Mutation probability:")
        self.mutation_probability_input = QLineEdit("0.1")
        self.mutation_probability_input.setValidator(self.positive_double_validator)
        self.initial_value_layout.addRow(self.mutation_probability_label, self.mutation_probability_input)

        self.mutation_probability_increase_label = QLabel("Increase by:")
        self.mutation_probability_increase_input = QLineEdit("0.05")
        self.mutation_probability_increase_input.setValidator(self.negative_double_validator)
        self.increase_value_layout.addRow(
            self.mutation_probability_increase_label, self.mutation_probability_increase_input
        )

        self.run_experiments_button = QPushButton("Run experiments")
        self.run_experiments_button.clicked.connect(self.run_experiments)
        self.experiment_settings_layout.addWidget(self.run_experiments_button)

        self.run_experiments_button = QPushButton("Run with all functions")
        self.run_experiments_button.clicked.connect(self.run_experiments_with_all_functions)
        self.experiment_settings_layout.addWidget(self.run_experiments_button)

        self.experiment_settings_layout.addStretch()

        self.settings = QSettings("window_cache.ini", QSettings.IniFormat)

        self.delete_results_button = QPushButton("Delete results")
        self.delete_results_button.clicked.connect(self.results_table.delete_all_results)
        self.central_layout.addWidget(self.delete_results_button)

    @Slot(QCheckBox)
    def filter_changed(self, checkbox: QCheckBox):
        category = checkbox.text()
        self.results_table.setColumnHidden(categories_to_index[category], not checkbox.isChecked())

    def add_results(self, results: list):
        self.results_table.add_results(results)

    def run_experiments_with_all_functions(self):
        self.all_experiment_settings = self.get_all_experiment_settings()
        self.create_progess_dialog(len(self.all_experiment_settings) * int(self.experiment_count_input.text()))
        self.run_experiment(self.all_experiment_settings)

    def get_all_experiment_settings(self) -> list[ExperimentSettings]:
        base_experiment_settings = self.get_experiment_settings()
        experiment_settings = []

        # Loop over all the function combinations
        function_combinations = product(
            ProgenitorSelectionFunction.get_functions(),
            MutationFunction.get_functions(),
            CrossoverFunction.get_functions(),
        )

        for progenitor_selection_function, mutation_function, crossover_function in function_combinations:
            settings = deepcopy(base_experiment_settings)
            settings.progenitor_selection_function = progenitor_selection_function
            settings.mutation_function = mutation_function
            settings.crossover_function = crossover_function
            experiment_settings.append(settings)

        return experiment_settings

    def get_experiment_settings(self) -> ExperimentSettings:
        experiment_count = int(self.experiment_count_input.text())
        seed = int(self.seed_input.text())

        datasets = {
            "Diabetes": "diabetes_normalized.dat",
            "Quake": "quake_normalized.dat",
            "Laser": "laser_normalized.dat",
        }
        dataset_filename = datasets.get(self.dataset_combobox.currentText())

        progenitor_selection_function = self.progenitor_selection_function_combobox.currentText()
        mutation_function = self.mutation_function_combobox.currentText()
        crossover_function = self.crossover_function_combobox.currentText()

        progenitor_selection_function = ProgenitorSelectionFunction.from_string(progenitor_selection_function)
        mutation_function = MutationFunction.from_string(mutation_function)
        crossover_function = CrossoverFunction.from_string(crossover_function)

        initial_individual_count = int(self.individual_count_input.text())
        individual_count_increase = int(self.individual_count_increase_input.text())
        initial_iterations = int(self.iterations_input.text())
        iterations_increase = int(self.iterations_increase_input.text())
        initial_crossover_probability = float(self.crossover_probability_input.text())
        crossover_probability_increase = float(self.crossover_probability_increase_input.text())
        initial_mutation_probability = float(self.mutation_probability_input.text())
        mutation_probability_increase = float(self.mutation_probability_increase_input.text())

        return ExperimentSettings(
            experiment_count=experiment_count,
            seed=seed,
            dataset_filename=dataset_filename,
            progenitor_selection_function=progenitor_selection_function,
            mutation_function=mutation_function,
            crossover_function=crossover_function,
            initial_individual_count=initial_individual_count,
            individual_count_increase=individual_count_increase,
            initial_iterations=initial_iterations,
            iterations_increase=iterations_increase,
            initial_crossover_probability=initial_crossover_probability,
            crossover_probability_increase=crossover_probability_increase,
            initial_mutation_probability=initial_mutation_probability,
            mutation_probability_increase=mutation_probability_increase,
        )

    def create_progess_dialog(self, steps: int):
        self.progress_dialog = QProgressDialog("Running experiments...", "Cancel", 0, 1, self)
        self.progress_dialog.setWindowTitle("Run experiments")
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        # Disable resizing of the progress dialog.
        self.progress_dialog.setFixedSize(self.progress_dialog.size())
        self.progress_dialog.canceled.connect(self.interrupt_experiments)
        self.progress_dialog.setMaximum(steps)

    def run_experiments(self):
        experiment_settings = self.get_experiment_settings()
        self.create_progess_dialog(experiment_settings.experiment_count)
        self.run_experiment([experiment_settings])

    def run_experiment(self, experiment_settings: list[ExperimentSettings]):
        self.experiment_thread = QThread()
        self.experiment_runner = ExperimentRunner(experiment_settings)
        self.experiment_runner.moveToThread(self.experiment_thread)

        self.experiment_thread.started.connect(self.experiment_runner.run)
        self.experiment_thread.finished.connect(self.progress_dialog.close)

        self.experiment_runner.finished.connect(self.experiment_thread.quit)
        self.experiment_runner.finished.connect(self.experiment_runner.deleteLater)
        self.experiment_runner.result_ready.connect(self.result_received)

        self.experiment_thread.start()
        self.progress_dialog.show()

    @Slot()
    def interrupt_experiments(self):
        self.experiment_thread.requestInterruption()

        self.progress_dialog.show()
        self.progress_dialog.setLabelText("Finishing last experiment")
        # Enable resizing of the progress dialog.

        self.progress_dialog.setRange(0, 0)

        self.progress_dialog.setCancelButtonText("Force quit")
        self.progress_dialog.canceled.disconnect(self.interrupt_experiments)
        self.progress_dialog.canceled.connect(self.force_quit)

    @Slot()
    def force_quit(self):
        if not self.experiment_thread.isRunning():
            return

        question = QMessageBox.question(
            self,
            "Force quit",
            "Are you sure you want to force quit? This may leave the program in an unstable state.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if question != QMessageBox.Yes:
            return

        if not self.experiment_thread.isRunning():
            return

        self.experiment_thread.terminate()

        self.progress_dialog.canceled.disconnect(self.force_quit)
        self.progress_dialog.close()

    @Slot(int, Result)
    def result_received(self, i: int, result: Result):
        if self.experiment_thread.isInterruptionRequested():
            return

        self.progress_dialog.setLabelText(f"Running experiment {i + 1}/{self.progress_dialog.maximum()}")
        self.progress_dialog.setValue(i)
        self.results_table.add_result(result)

    def show_plot(self, plot: PIL.Image.Image):
        plot_window = PlotWindow(self, plot)
        plot_window.move(self.pos() + QPoint(50, 50))
        plot_window.show()

    def showEvent(self, event: QShowEvent):
        QMainWindow.showEvent(self, event)

        try:
            with open("settings.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            # No config file, use defaults
            return

        for i, category in enumerate(config["categories"]):
            self.filters_checkboxes[i].setChecked(category["enabled"])

        parameters = {key: str(value) for key, value in config["parameters"].items()}

        self.dataset_combobox.setCurrentText(parameters["dataset"])
        self.experiment_count_input.setText(parameters["experiment_count"])
        self.seed_input.setText(parameters["seed"])

        self.progenitor_selection_function_combobox.setCurrentText(parameters["progenitor_selection_function"])
        self.mutation_function_combobox.setCurrentText(parameters["mutation_function"])
        self.crossover_function_combobox.setCurrentText(parameters["crossover_function"])

        self.individual_count_input.setText(parameters["individual_count"])
        self.individual_count_increase_input.setText(parameters["individual_count_increase"])
        self.iterations_input.setText(parameters["iterations"])
        self.iterations_increase_input.setText(parameters["iterations_increase"])
        self.crossover_probability_input.setText(parameters["crossover_probability"])
        self.crossover_probability_increase_input.setText(parameters["crossover_probability_increase"])
        self.mutation_probability_input.setText(parameters["mutation_probability"])
        self.mutation_probability_increase_input.setText(parameters["mutation_probability_increase"])

        # Load state of the window
        window_state = self.settings.value("window_state", self.saveState())
        window_geometry = self.settings.value("window_geometry", self.saveGeometry())

        if window_state is not None and window_geometry is not None:
            self.restoreState(window_state)
            self.restoreGeometry(window_geometry)
        else:
            print(f"{window_state is None=}, {window_geometry is None=}")

    def get_config(self) -> dict:
        config = {
            "categories": [],
        }

        for checkbox in self.filters_checkboxes:
            config["categories"].append(
                {
                    "name": checkbox.text(),
                    "enabled": checkbox.isChecked(),
                }
            )

        config["parameters"] = {
            "dataset": self.dataset_combobox.currentText(),
            "experiment_count": self.experiment_count_input.text(),
            "seed": self.seed_input.text(),
            "mutation_function": self.mutation_function_combobox.currentText(),
            "crossover_function": self.crossover_function_combobox.currentText(),
            "progenitor_selection_function": self.progenitor_selection_function_combobox.currentText(),
            "individual_count": self.individual_count_input.text(),
            "individual_count_increase": self.individual_count_increase_input.text(),
            "iterations": self.iterations_input.text(),
            "iterations_increase": self.iterations_increase_input.text(),
            "crossover_probability": self.crossover_probability_input.text(),
            "crossover_probability_increase": self.crossover_probability_increase_input.text(),
            "mutation_probability": self.mutation_probability_input.text(),
            "mutation_probability_increase": self.mutation_probability_increase_input.text(),
        }

        self.settings.setValue("window_state", self.saveState())
        self.settings.setValue("window_geometry", self.saveGeometry())

        return config

    def closeEvent(self, event: QCloseEvent) -> None:
        with open("settings.json", "w") as f:
            json.dump(self.get_config(), f, indent=4)
        QMainWindow.closeEvent(self, event)
