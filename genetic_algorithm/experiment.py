import io

import matplotlib.pyplot as plt
import numpy as np

from genetic_algorithm.genetic_functions import create_population, read_dat, fitness_function, NamedFunction
from genetic_algorithm.result import Result


def run_experiment(
    dataset_filename: str,
    seed: int,
    individual_count: int,
    iterations: int,
    progenitor_selection_function: NamedFunction,
    mutation_function: NamedFunction,
    crossover_function: NamedFunction,
    crossover_probability: float,
    mutation_probability: float,
) -> Result:
    np.random.seed(seed)

    crossover_probability = round(crossover_probability, 5)
    mutation_probability = round(mutation_probability, 5)

    data = read_dat(dataset_filename)

    population = create_population(data, individual_count)
    best_fitnesses = np.ndarray(shape=(iterations,), dtype=np.float64)
    average_fitnesses = np.ndarray(shape=(iterations,), dtype=np.float64)

    for i in range(iterations):
        progenitors = progenitor_selection_function(data, population, individual_count, individual_count // 2)

        children = crossover_function(progenitors, crossover_probability)

        children = mutation_function(children, mutation_probability)
        population = np.concatenate((progenitors, children))
        fitnesses = fitness_function(data, population)

        best_fitnesses[i] = np.min(fitnesses)
        average_fitnesses[i] = np.mean(fitnesses)

    x = np.arange(len(best_fitnesses))
    fig, ax = plt.subplots()

    ax.plot(x, best_fitnesses, label="Best fitnesses", color="red")
    ax.plot(x, average_fitnesses, label="Average fitnesses", color="green")

    ax.legend(loc="upper right")

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Fitness")
    ax.set_title(
        f"{iterations} iterations, {individual_count} individuals, {crossover_function.name} crossover,\n"
        f"{mutation_function.name} mutation, {progenitor_selection_function.name} progenitor selection,\n"
        f"{crossover_probability * 100}% crossover, {mutation_probability * 100}% mutation, {seed} seed",
        fontsize=10,
    )

    best_fitness = np.min(best_fitnesses)

    plot_buffer = io.BytesIO()
    plt.savefig(plot_buffer, format="png")
    plot_buffer.seek(0)

    fitnesses = fitness_function(data, population)
    best_individual = population[np.argmin(fitnesses)]
    best_individual_string = np.array2string(best_individual, precision=5, separator=",")

    result = Result(
        dataset_filename,
        seed,
        individual_count,
        iterations,
        crossover_probability,
        mutation_probability,
        progenitor_selection_function,
        crossover_function,
        mutation_function,
        best_fitness,
        best_individual_string,
        plot_buffer,
    )

    plt.close()
    return result
