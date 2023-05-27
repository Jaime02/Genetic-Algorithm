from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


class NamedFunction:
    def __init__(self, name: str, function: Callable):
        self.name = name
        self.function = function

    def __str__(self):
        return self.name

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class ProgenitorSelectionFunction:
    @staticmethod
    def get_functions() -> list[NamedFunction]:
        return [
            ProgenitorSelectionFunction.roulette(),
            ProgenitorSelectionFunction.tournament_with_replacement(),
            ProgenitorSelectionFunction.tournament_without_replacement(),
        ]

    @staticmethod
    def from_string(name: str) -> NamedFunction:
        if name == "Roulette":
            return ProgenitorSelectionFunction.roulette()
        if name == "Tournament with replacement":
            return ProgenitorSelectionFunction.tournament_with_replacement()
        if name == "Tournament without replacement":
            return ProgenitorSelectionFunction.tournament_without_replacement()

        raise ValueError(f"Invalid name for selection function: {name}")

    @staticmethod
    def roulette() -> NamedFunction:
        return NamedFunction("Roulette", ProgenitorSelectionFunction._selection_roulette)

    @staticmethod
    def tournament_with_replacement() -> NamedFunction:
        return NamedFunction("Tournament with replacement", ProgenitorSelectionFunction._selection_tournament_replacement)

    @staticmethod
    def tournament_without_replacement() -> NamedFunction:
        return NamedFunction("Tournament without replacement", ProgenitorSelectionFunction._selection_tournament_no_replacement)

    @staticmethod
    def _selection_roulette(data: np.ndarray, population: np.ndarray, individuals: int, k_group: int) -> np.ndarray:
        fitnesses = 1 / fitness_function(data, population)
        chances = fitnesses / np.sum(fitnesses)

        indexes = np.random.choice(population.shape[0], size=individuals, replace=False, p=chances)
        return population[indexes]

    @staticmethod
    def _selection_tournament_replacement(
            data: np.ndarray, population: np.ndarray, individuals: int, k_group: int
    ):
        fitnesses = fitness_function(data, population)

        progenitors = np.zeros(shape=(individuals, population.shape[1]), dtype=np.float64)
        for i in range(individuals):
            # Get a random sample of the population
            indexes = np.random.choice(population.shape[0], size=k_group, replace=False)
            fighters = population[indexes]
            # Get the best individual
            best = np.argmin(fitnesses[indexes])
            progenitors[i] = fighters[best]

        return progenitors

    @staticmethod
    def _selection_tournament_no_replacement(
            data: np.ndarray, population: np.ndarray, individuals: int, k_group: int
    ):
        fitnesses = fitness_function(data, population)

        available = np.arange(population.shape[0])

        progenitors = np.zeros(shape=(individuals, population.shape[1]), dtype=np.float64)
        for i in range(individuals):
            # Get a random sample of the population
            size = k_group if k_group < len(available) else len(available)

            indexes = np.random.choice(available, size=size, replace=False)
            fighters = population[indexes]
            # Get the best individual
            best = np.argmin(fitnesses[indexes])
            progenitors[i] = fighters[best]
            available = np.delete(available, best)

        assert len(progenitors) == individuals
        return progenitors


class MutationFunction:
    @staticmethod
    def get_functions() -> list[NamedFunction]:
        return [
            MutationFunction.uniform(),
            MutationFunction.non_uniform(),
        ]

    @staticmethod
    def from_string(name: str) -> NamedFunction:
        if name == "Uniform":
            return MutationFunction.uniform()
        if name == "Non-uniform":
            return MutationFunction.non_uniform()

        raise ValueError(f"Invalid name for mutation function: {name}")

    @staticmethod
    def uniform() -> NamedFunction:
        return NamedFunction("Uniform", MutationFunction._uniform)
    
    @staticmethod
    def non_uniform() -> NamedFunction:
        return NamedFunction("Non-uniform", MutationFunction._non_uniform)

    @staticmethod
    def _uniform(population: np.ndarray, mutation_probability: float) -> np.ndarray:
        mutated_indexes = np.random.rand(*population.shape) < mutation_probability
        return np.where(mutated_indexes, np.random.rand(*population.shape), population)

    @staticmethod
    def _non_uniform(population: np.ndarray, mutation_probability: float) -> np.ndarray:
        mutated_indexes = np.random.rand(*population.shape) < mutation_probability

        mutated_population = population.copy()
        indices = np.where(mutated_indexes)
        num_mutations = len(indices[0])

        other_i = np.random.randint(0, population.shape[0], size=num_mutations)
        other_j = np.random.randint(0, population.shape[1], size=num_mutations)

        parent_1 = population[indices]
        parent_2 = population[other_i, other_j]

        mutated_data = (parent_1 + parent_2) / 2
        mutated_population[indices] = mutated_data
        return mutated_population


class CrossoverFunction:
    @staticmethod
    def get_functions() -> list[NamedFunction]:
        return [
            CrossoverFunction.single_point(),
            CrossoverFunction.two_points(),
        ]

    @staticmethod
    def from_string(name: str) -> NamedFunction:
        if name == "Single point":
            return CrossoverFunction.single_point()
        if name == "Two points":
            return CrossoverFunction.two_points()

        raise ValueError(f"Invalid name for crossover function: {name}")

    @staticmethod
    def single_point() -> NamedFunction:
        return NamedFunction("Single point", CrossoverFunction._single_point)
        
    @staticmethod
    def two_points() -> NamedFunction:
        return NamedFunction("Two point", CrossoverFunction._two_points)
    
    @staticmethod
    def _single_point(progenitors: np.ndarray, crossover_probability: float) -> np.ndarray:
        # Crossover
        children = progenitors.copy()

        end = progenitors.shape[0]
        if progenitors.shape[0] % 2 == 1:
            end -= 1

        for i in range(0, end, 2):
            if np.random.rand() < crossover_probability:
                # Crossover
                child_1 = progenitors[i].copy()
                child_2 = progenitors[i + 1].copy()

                # Get a random crossover point
                crossover_point = np.random.randint(0, progenitors.shape[1])

                # Swap data
                child_1[crossover_point:] = progenitors[i + 1, crossover_point:]
                child_2[crossover_point:] = progenitors[i, crossover_point:]

                children[i] = child_1
                children[i + 1] = child_2

        return children

    @staticmethod
    def _two_points(progenitors: np.ndarray, crossover_probability: float) -> np.ndarray:
        # Crossover
        children = progenitors.copy()
        for i in range(0, progenitors.shape[0], 2):
            if np.random.rand() < crossover_probability:
                # Crossover
                child_1 = progenitors[i].copy()
                child_2 = progenitors[i + 1].copy()

                # Get a random crossover point
                crossover_point_1 = np.random.randint(0, progenitors.shape[1])
                crossover_point_2 = np.random.randint(crossover_point_1, progenitors.shape[1])

                # Swap data
                child_1[crossover_point_1:crossover_point_2] = progenitors[i + 1, crossover_point_1:crossover_point_2]
                child_2[crossover_point_1:crossover_point_2] = progenitors[i, crossover_point_1:crossover_point_2]

                children[i] = child_1
                children[i + 1] = child_2

        return children


def read_dat(filename: str) -> np.ndarray:
    file = Path(__file__).parent / "datasets" / filename
    dataframe = pd.read_csv(file, sep=",")
    # drop first column
    dataframe = dataframe.drop(dataframe.columns[0], axis=1)
    return dataframe.to_numpy()


def create_population(data: np.ndarray, individuals: int) -> np.ndarray:
    return np.random.rand(individuals, data.shape[1])


def fitness_function(data: np.ndarray, population: np.ndarray) -> np.ndarray:
    fitnesses = np.zeros(shape=(population.shape[0],), dtype=np.float64)

    for i in range(population.shape[0]):
        individual = population[i]
        destinos = individual[0] + np.dot(data[:, :-1], individual[1:])
        fitnesses[i] = np.mean((data[:, -1] - destinos) ** 2)

    return fitnesses
