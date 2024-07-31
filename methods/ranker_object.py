import json
import time
import numpy as np
import random
from pymoo.core.variable import Real, Integer, Choice, Binary
from pymoo.core.problem import ElementwiseProblem
from pymoo.visualization.scatter import Scatter
from pymoo.algorithms.moo.nsga2 import NSGA2, RankAndCrowdingSurvival
from pymoo.core.mixed import MixedVariableMating, MixedVariableGA, MixedVariableSampling, MixedVariableDuplicateElimination
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.operators.crossover.ox import OrderCrossover
from pymoo.operators.mutation.inversion import InversionMutation
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.operators.crossover.ox import random_sequence
from pymoo.operators.mutation.inversion import inversion_mutation
from pymoo.termination.ftol import MultiObjectiveSpaceTermination

from greedy_steps_optimizer import GreedyStepsOptimizer
from greedy_segments_optimizer import GreedySegmentsOptimizer

from pymoo.algorithms.moo.sms import SMSEMOA

import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from evaluation_utils import APFD, APSD, APOD, APOTD, APSBD, fault_coverage, segment_coverage, object_coverage, object_type_coverage, sibling_coverage
from models.test_suite import TestSuite
# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite


class PartiallyMappedCrossover(Crossover):
    # In the crossover, an offspring 𝑜 is formed from two selected parents 𝑝1 and 𝑝2 , with the size of N, as follows:
    # (i) select a random position 𝑐 in 𝑝1 as the cut point; (ii) the first 𝑐 elements of 𝑝1 are selected as the first
    # 𝑐 elements of 𝑜; (iii) extract the 𝑁 − 𝑐 elements in 𝑝2 that are not in 𝑜 yet and put them as the last 𝑁 − 𝑐
    # elements of 𝑜.
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


class TestCaseRankerObject(ElementwiseProblem):

    def __init__(self, **kwargs):
        self.test_suite = kwargs.get("test_suite", None)
        number_of_test_cases = len(self.test_suite.test_cases)

        self.baseline_segment_dict = segment_coverage(self.test_suite)
        self.baseline_object_dict = object_coverage(self.test_suite)
        self.baseline_object_type_dict = object_type_coverage(self.test_suite)
        self.baseline_sibling_dict = sibling_coverage(self.test_suite)

        lowest_tc_index = 0
        highest_tc_index = number_of_test_cases - 1

        super().__init__(n_var=number_of_test_cases, n_obj=1,
                         xl=lowest_tc_index, xu=highest_tc_index, **kwargs)

    # def func1(self, x):
    #     return sum(list(x.values()))

    def func2(self, x):
        # x is a dictionary
        apsd = APSD(x, self.test_suite)
        return -apsd

    def func3(self, x):
        # x is a dictionary
        apod = APOD(x, self.test_suite)
        return -apod


    def func4(self, x):
        # # x is a dictionary
        apotd = APOTD(x, self.test_suite)
        return -apotd

    def func5(self, x):
        # x is a dictionary
        apsbd = APSBD(x, self.test_suite)
        return -apsbd


    def _evaluate(self, x, out, *args, **kwargs):
        apod = self.func3(x)

        out['F'] = [apod]
        return out['F']

