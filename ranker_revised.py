import json
import time
import numpy as np
import random
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.operators.crossover.ox import random_sequence
from pymoo.operators.mutation.inversion import inversion_mutation
from pymoo.algorithms.moo.age import AGEMOEA
from pymoo.algorithms.moo.age2 import AGEMOEA2
from methods.fast_optimizer import FASTOptimizer

from methods.greedy_objects_optimizer import GreedyObjectsOptimizer
from methods.pmx import PMXCrossover 
from methods.hybrid_mut import HybridMut

from methods.genetic_algorithm_utils import sort_genetic_solutions

import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from methods.evaluation_utils import APFD, APFDc, APSD, APOD, APOTD, APSBD, fault_coverage, segment_coverage, object_coverage, object_type_coverage, sibling_coverage, percentage_of_test_case_for_100_fault_coverage
from models.test_suite import TestSuite
from methods.terminator import Terminator
from merge_csv_eval import main as merge_csv_eval_main
import future
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite


class PartiallyMappedCrossover(Crossover):
    def __init__(self, **kwargs):
        super().__init__(n_parents=2, n_offsprings=1, **kwargs)

    def _do(self, _, X, **kwargs):

        # get the X of parents and count the matings
        _, n_matings, n_var = X.shape

        # the array where the offsprings will be stored to
        Y = np.full(shape=(self.n_offsprings, n_matings, n_var),
                    fill_value=-1, dtype=X.dtype)

        for i in range(n_matings):
            parent_1 = X[0, i]
            parent_2 = X[1, i]
            offspring = []

            # Take the first c elements of the first parent and put them in the offspring.
            cut_point = np.random.randint(0, n_var)
            for j in range(cut_point):
                offspring.append(parent_1[j])

            # Take the elements of the second parent that are not in the offspring and put them in the offspring,
            # keeping them in the same order.
            for k in range(n_var):
                if parent_2[k] not in offspring:
                    offspring.append(parent_2[k])

            # Put the offspring in the offspring array.
            Y[0, i, :] = offspring[:]

        return Y


class MultipleMutation(Mutation):

    def _do(self, problem, X, **kwargs):
        mutation_operators = [self.swap_mutation,
                              self.invert_mutation, self.insert_mutation]

        Y = X.copy()
        for i, y in enumerate(X):
            # Has a 0.33 chance of doing a random mutation of SWAP, INVERT or INSERT mutation.
            mutation_operator = np.random.choice(mutation_operators)
            Y[i] = mutation_operator(y)
        return Y

    def swap_mutation(self, y):
        # This mutation operator randomly selects two positions in a chromosome 𝑝 and swaps the index of two genes (test
        # case indexes in the order) to generate a new offspring
        n_var = len(y)
        i = np.random.randint(0, n_var)
        j = np.random.randint(0, n_var)
        temp = y[i]
        y[i] = y[j]
        y[j] = temp
        return y

    def invert_mutation(self, y):
        # This mutation randomly selects a subsequence of length 𝑁 in the chromosome 𝑝 and reverses the order of the
        # genes in the subsequence to generate a new offspring
        n_var = len(y)
        seq = random_sequence(n_var)
        return inversion_mutation(y, seq, inplace=True)

    def insert_mutation(self, y):
        # This mutation randomly selects a gene in the chromosome 𝑝 and moves it to another index in the solution to
        # generate a new offspring
        n_var = len(y)
        i = np.random.randint(0, n_var)
        j = np.random.randint(0, n_var)
        gene = y[i]
        y = np.delete(y, i)
        return np.insert(y, j, gene)


class TestCaseRanker(ElementwiseProblem):

    def __init__(self, **kwargs):
        self.test_suite = kwargs.get("test_suite", None)
        number_of_test_cases = len(self.test_suite.test_cases)

        self.baseline_segment_dict = segment_coverage(self.test_suite)
        self.baseline_object_dict = object_coverage(self.test_suite)
        self.baseline_object_type_dict = object_type_coverage(self.test_suite)
        self.baseline_sibling_dict = sibling_coverage(self.test_suite)

        _, self.greedy_object_ordering = GreedyObjectsOptimizer(test_suite).optimize()


        lowest_tc_index = 0
        highest_tc_index = number_of_test_cases - 1

        super().__init__(n_var=number_of_test_cases, n_obj=4,
                         xl=lowest_tc_index, xu=highest_tc_index, 
                         **kwargs)

    # def func1(self, x):
    #     return sum(list(x.values()))

    def func2(self, x):
        apsd = APSD(x, self.test_suite)
        return -apsd

    def func3(self, x):
        apod = APOD(x, self.test_suite)
        return -apod

    def func4(self, x):
        apotd = APOTD(x, self.test_suite)
        return -apotd

    def func5(self, x):
        apsbd = APSBD(x, self.test_suite)
        return -apsbd
    
    def func6(self, x):
        #calculate distance between x and greedy object ordering
        x = list(x)
        distance = 0
        set2 = self.greedy_object_ordering
        for i in range(len(x)):
            distance += abs(i - set2.index(x[i]))*(len(set2) - i)

        distance /= len(x)*(len(x) - 1)/2
        return distance


    def _evaluate(self, x, out, *args, **kwargs):
        apsd = self.func2(x)
        apod = self.func3(x)
        apotd = self.func4(x)
        apsbd = self.func5(x)
        out['F'] = [apsd,
            apod, 
            apotd, 
            apsbd,
            ]



def best_order(testsuite):
    fault_coverage_dict = fault_coverage(testsuite)
    order = []
    for fault_type, test_cases in fault_coverage_dict.items():
        if len(test_cases) > 0:
            first_test_case = test_cases[0]
            rest_test_cases = [] if len(test_cases) == 1 else test_cases[1:]
            #add the first test case to the first position
            order.insert(0, first_test_case)
            #add the rest test cases to the end of the list
            order.extend(rest_test_cases)
    for i in range(len(testsuite.test_cases)):
        if i not in order:
            order.append(i)
    return order

def worst_order(testsuite):
    fault_coverage_dict = fault_coverage(testsuite)
    order = []
    for fault_type, test_cases in fault_coverage_dict.items():
        order.extend(test_cases)
    for i in range(len(testsuite.test_cases)):
        if i not in order:
            order.insert(0, i)
    return order

def get_solution_object(order, testsuite):
    solution_object = {}
    # solution_object["mask"] = order
    #if order is np array, convert it to list
    if isinstance(order, np.ndarray):
        order = order.tolist()
    solution_object["mask"] = order
    solution_object["APFD"] = APFD(order, testsuite)
    solution_object["APFDC"] = APFDc(order, testsuite)
    solution_object["APSD"] = APSD(order, testsuite)
    solution_object["APOD"] = APOD(order, testsuite)
    solution_object["APOTD"] = APOTD(order, testsuite)
    solution_object["APSBD"] = APSBD(order, testsuite)
    solution_object["faults"] = [0 if len(testsuite.test_cases[i].failures) == 0 else testsuite.test_cases[i].failures[0]
                            for i in order]
    solution_object["WFC"] = percentage_of_test_case_for_100_fault_coverage(order, testsuite)
    return solution_object

def export_solutions_csv(solutions, file_name):
    df = pd.DataFrame.from_dict(solutions, orient="index")
    if "mask" in df.columns:
        df = df.drop(columns=["mask"])
    if "masks" in df.columns:
        df = df.drop(columns=["masks"])
    if "faults" in df.columns:
        df = df.drop(columns=["faults"])
    # df = df.drop(columns=["mask", "masks", "faults"])
    #set index name
    df.index.name = "solution"
    #add average column to the end as the average of apsd, apod, apotd, apsbd
    df["average"] = df[["APSD", "APOD", "APOTD", "APSBD"]].mean(axis=1)
    df.to_csv(file_name)

def best_pareto_solution(resF, resX):
    #sort the solutions by apsd and apod
    #the first solution is the best
    sorted_solutions = sorted(zip(resF, resX), key=lambda x: (x[0][0], x[0][1]))
    chosen_solution = sorted_solutions[0][1]
    chosen_solution = sort_genetic_solutions(chosen_solution, test_suite)
    return chosen_solution

def get_random_solution(test_suite, random_times):
    sum_apfd, sum_apfdc, sum_apsd, sum_apod, sum_apotd, sum_apsbd = 0, 0, 0, 0, 0, 0
    sum_wfc = 0
    masks = []
    for i in range(random_times):
        random_order_solution = list(range(len(test_suite.test_cases)))
        random.shuffle(random_order_solution)
        random_solution = get_solution_object(random_order_solution, test_suite)
        sum_apfd += random_solution["APFD"]
        sum_apfdc += random_solution["APFDC"]
        sum_apsd += random_solution["APSD"]
        sum_apod += random_solution["APOD"]
        sum_apotd += random_solution["APOTD"]
        sum_apsbd += random_solution["APSBD"]
        sum_wfc += random_solution["WFC"]
        masks.append(random_order_solution)
    
    
    random_solution = {
        "APFD": sum_apfd/random_times,
        "APFDC": sum_apfdc/random_times,
        "APSD": sum_apsd/random_times,
        "APOD": sum_apod/random_times,
        "APOTD": sum_apotd/random_times,
        "APSBD": sum_apsbd/random_times,
        "WFC": sum_wfc/random_times,
        "masks": masks,
    }
    return random_solution

def get_greedy_object_solution(test_suite, times=10):
    sum_apfd, sum_apfdc, sum_apsd, sum_apod, sum_apotd, sum_apsbd = 0, 0, 0, 0, 0, 0
    sum_wfc = 0
    for i in range(times):
        greedy_object_order, greedy_object_ordering = GreedyObjectsOptimizer(test_suite).optimize()
        greedy_object_solution = get_solution_object(greedy_object_ordering, test_suite)
        sum_apfd += greedy_object_solution["APFD"]
        sum_apfdc += greedy_object_solution["APFDC"]
        sum_apsd += greedy_object_solution["APSD"]
        sum_apod += greedy_object_solution["APOD"]
        sum_apotd += greedy_object_solution["APOTD"]
        sum_apsbd += greedy_object_solution["APSBD"]
        sum_wfc += greedy_object_solution["WFC"]


    greedy_object_solution = {
        "APFD": sum_apfd/times,
        "APFDC": sum_apfdc/times,
        "APSD": sum_apsd/times,
        "APOD": sum_apod/times,
        "APOTD": sum_apotd/times,
        "APSBD": sum_apsbd/times,
        "WFC": sum_wfc/times,
        "mask": greedy_object_ordering,
    }
    return greedy_object_solution

def get_time_based_solution(test_suite):
    #sort the test cases by time
    test_cases = test_suite.test_cases
    time_based_order = sorted(range(len(test_cases)), key=lambda i: test_cases[i].duration)
    time_based_solution = get_solution_object(time_based_order, test_suite)
    return time_based_solution

def get_fast_solutions(test_suite_file, repeats=10):
    fast_solutions, ga_solutions, ga_s_solutions, gt_solutions, artf_solutions = [], [], [], [], []
    for i in range(repeats):
        fast_optimizer = FASTOptimizer(test_suite_file)
        fast_solution = fast_optimizer.fast_optimize()
        fast_solution_object = get_solution_object(fast_solution, test_suite)
        fast_solutions.append(fast_solution_object)

        ga_solution = fast_optimizer.ga_optimize()
        ga_solution_object = get_solution_object(ga_solution, test_suite)
        ga_solutions.append(ga_solution_object)

        ga_s_solution = fast_optimizer.ga_s_optimize()
        ga_s_solution_object = get_solution_object(ga_s_solution, test_suite)
        ga_s_solutions.append(ga_s_solution_object)

        gt_solution = fast_optimizer.gt_optimize()
        gt_solution_object = get_solution_object(gt_solution, test_suite)
        gt_solutions.append(gt_solution_object)

        artf_solution = fast_optimizer.artf_optimize()
        artf_solution_object = get_solution_object(artf_solution, test_suite)
        artf_solutions.append(artf_solution_object)

    print("fast_solutions", fast_solutions)
    print("ga_solutions", ga_solutions)
    print("ga_s_solutions", ga_s_solutions)

    fast_solution = {
        "APFD": sum([x["APFD"] for x in fast_solutions])/repeats,
        "APFDC": sum([x["APFDC"] for x in fast_solutions])/repeats,
        "APSD": sum([x["APSD"] for x in fast_solutions])/repeats,
        "APOD": sum([x["APOD"] for x in fast_solutions])/repeats,
        "APOTD": sum([x["APOTD"] for x in fast_solutions])/repeats,
        "APSBD": sum([x["APSBD"] for x in fast_solutions])/repeats,
        "WFC": sum([x["WFC"] for x in fast_solutions])/repeats,
        "masks": [x["mask"] for x in fast_solutions],
    }

    ga_solution = {
        "APFD": sum([x["APFD"] for x in ga_solutions])/repeats,
        "APFDC": sum([x["APFDC"] for x in ga_solutions])/repeats,
        "APSD": sum([x["APSD"] for x in ga_solutions])/repeats,
        "APOD": sum([x["APOD"] for x in ga_solutions])/repeats,
        "APOTD": sum([x["APOTD"] for x in ga_solutions])/repeats,
        "APSBD": sum([x["APSBD"] for x in ga_solutions])/repeats,
        "WFC": sum([x["WFC"] for x in ga_solutions])/repeats,
        "masks": [x["mask"] for x in ga_solutions],
        "faults": ga_solutions[0]["faults"],
    }

    ga_s_solution = {
        "APFD": sum([x["APFD"] for x in ga_s_solutions])/repeats,
        "APFDC": sum([x["APFDC"] for x in ga_s_solutions])/repeats,
        "APSD": sum([x["APSD"] for x in ga_s_solutions])/repeats,
        "APOD": sum([x["APOD"] for x in ga_s_solutions])/repeats,
        "APOTD": sum([x["APOTD"] for x in ga_s_solutions])/repeats,
        "APSBD": sum([x["APSBD"] for x in ga_s_solutions])/repeats,
        "WFC": sum([x["WFC"] for x in ga_s_solutions])/repeats,
        "masks": [x["mask"] for x in ga_s_solutions],
        "faults": ga_s_solutions[0]["faults"],
    }

    gt_solution = {
        "APFD": sum([x["APFD"] for x in gt_solutions])/repeats,
        "APFDC": sum([x["APFDC"] for x in gt_solutions])/repeats,
        "APSD": sum([x["APSD"] for x in gt_solutions])/repeats,
        "APOD": sum([x["APOD"] for x in gt_solutions])/repeats,
        "APOTD": sum([x["APOTD"] for x in gt_solutions])/repeats,
        "APSBD": sum([x["APSBD"] for x in gt_solutions])/repeats,
        "WFC": sum([x["WFC"] for x in gt_solutions])/repeats,
        "masks": [x["mask"] for x in gt_solutions],
        "faults": gt_solutions[0]["faults"],
    }

    artf_solution = {
        "APFD": sum([x["APFD"] for x in artf_solutions])/repeats,
        "APFDC": sum([x["APFDC"] for x in artf_solutions])/repeats,
        "APSD": sum([x["APSD"] for x in artf_solutions])/repeats,
        "APOD": sum([x["APOD"] for x in artf_solutions])/repeats,
        "APOTD": sum([x["APOTD"] for x in artf_solutions])/repeats,
        "APSBD": sum([x["APSBD"] for x in artf_solutions])/repeats,
        "WFC": sum([x["WFC"] for x in artf_solutions])/repeats,
        "masks": [x["mask"] for x in artf_solutions],
    }

    return fast_solution, ga_solution, ga_s_solution, gt_solution, artf_solution

if __name__ == "__main__":
    # random.seed(1)
    files = os.listdir("data/test_suite_annotated")
    files = [file for file in files if file.endswith(".json")]
    random.seed(1)
    population_size = 100
    number_of_generations = 200
    crossover_probability = 0.5
    processed_files = []
    apfds = []
    apfdcs = []
    apsds = []
    apods = []
    apotds = []
    apsbds = []
    # format time as dd-mm-YY H:M:S
    cur_time = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())
    approach = "all"
    run_folder = f"data/solutions/solutions-{approach}-{cur_time}"
    for file in files:
        print("Processing", file)
        algorithms = [
            NSGA2(pop_size=population_size, sampling=PermutationRandomSampling(
            ), crossover=PartiallyMappedCrossover(prob=crossover_probability), mutation=MultipleMutation(),),
            AGEMOEA(pop_size=population_size, sampling=PermutationRandomSampling(
            ), crossover=PartiallyMappedCrossover(prob=crossover_probability), mutation=MultipleMutation(),),
            AGEMOEA2(pop_size=population_size, sampling=PermutationRandomSampling(
            ), crossover=PartiallyMappedCrossover(prob=crossover_probability), mutation=MultipleMutation(),),
        ]
        prefixes = [
                    "NSGA2", 
                    "AGEMOEA", 
                    "AGEMOEA2"
                    ]
        file = os.path.join(f"data/test_suite_annotated", file)
        folder_name = file.replace(".json", "").replace("data/test_suite_annotated", run_folder)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        test_suite = parse_test_suite_from_file(file)
        # test_suite.shuffle()
        # crawl_paths = test_suite.get_crawl_paths()
        export_file = os.path.join(folder_name, "all_solutions.json")
        solutions = {}

        for algorithm, prefix in zip(algorithms, prefixes):
            problem = TestCaseRanker(
                test_suite=test_suite)

            start = time.time()

            res = minimize(problem,
                           algorithm,
                           ('n_gen', number_of_generations),
                            # termination,
                           seed=1,
                           verbose=True)
            end = time.time()
            
            for i in range(len(res.X)):
                mask = res.X[i]
                mask = sort_genetic_solutions(mask, test_suite)
                solutions[i] =  get_solution_object(mask, test_suite)

            best_pareto_sol = best_pareto_solution(res.F, res.X)
            solutions[f"segment_based_{prefix}"] = get_solution_object(best_pareto_sol, test_suite)
            
        best_order_solution = best_order(test_suite)
        best_solution = get_solution_object(best_order_solution, test_suite)
        solutions["best"] = best_solution

        worst_order_solution = worst_order(test_suite)
        worst_solution = get_solution_object(worst_order_solution, test_suite)
        solutions["worst"] = worst_solution

        solutions["random"] = get_random_solution(test_suite, len(test_suite.test_cases))
        
        _, terminator_order = Terminator(test_suite).optimize()
        solutions["terminator"] = get_solution_object(terminator_order, test_suite)

        # solutions["time_based"] = get_time_based_solution(test_suite)

        fast_solution, ga_solution, ga_s_solution, gt_solution, artf_solution = get_fast_solutions(file, repeats=10)
        solutions["fast"] = fast_solution
        solutions["ga"] = ga_solution
        solutions["ga_s"] = ga_s_solution
        solutions["gt"] = gt_solution
        solutions["artf"] = artf_solution


        sorted_solutions = sorted(
            solutions.items(), key=lambda x: x[1]["APFD"], reverse=True)
            
        with open(export_file, "w") as f:
            # format the json file, if array, then an array will be in one line
            json.dump(sorted_solutions, f, indent=2)
        export_solutions_csv(solutions, os.path.join(folder_name, "all_solutions.csv"))
        processed_files.append({
            "test_suite_file": file,
            "solution_file": export_file,
        })

    with open("data/processed_files.json", "w") as f:
        json.dump(processed_files, f, indent=2)
    
    merge_csv_eval_main(run_folder)
