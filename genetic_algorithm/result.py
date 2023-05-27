import hashlib
import io
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

from genetic_algorithm.genetic_functions import NamedFunction


@dataclass
class Result:
    dataset: str
    seed: int
    individual_count: int
    iterations: int
    crossover_probability: float
    mutation_probability: float
    progenitor_selection_function: NamedFunction
    crossover_function: NamedFunction
    mutation_function: NamedFunction
    best_fitness: float
    best_individual: str
    plot: io.BytesIO

    @staticmethod
    def read_result(path: Path) -> "Result":
        return pickle.load(open(path, "rb"))

    def save(self):
        result_hash = self.calculate_hash()
        filename = f"results/{result_hash}.pickle"
        pickle.dump(self, open(filename, "wb"))

    @staticmethod
    def read_all_results() -> list["Result"]:
        try:
            os.mkdir("../results")
        except FileExistsError:
            pass

        paths = (Path().parent / "results").glob("*.pickle")
        return [Result.read_result(path) for path in paths]

    def to_list(self):
        return [
            self.dataset,
            self.seed,
            self.individual_count,
            self.iterations,
            self.crossover_probability,
            self.mutation_probability,
            self.progenitor_selection_function,
            self.crossover_function,
            self.mutation_function,
            self.best_fitness,
            self.best_individual,
        ]

    def calculate_hash(self):
        concatenated_str = ",".join([str(result) for result in self.to_list()])
        return hashlib.sha256(concatenated_str.encode()).hexdigest()
