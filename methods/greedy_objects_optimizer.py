import json
import os
import random
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from models.test_suite import TestSuite
from methods.evaluation_utils import APFD


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite
    

class GreedyObjectsOptimizer():
    def __init__(self, testsuite: TestSuite):
        self.testsuite = testsuite
        self.ordered_test_cases = []
        self.ordering = []
        self.coverred_objects = set()

    def get_covering_objects(self, tc):
        coverred_objects = set()
        for interaction, j in zip(tc.interactions, range(len(tc.interactions))):
            state = tc.states[j]
            key = (state.url, interaction.test_object.xpath)
            if key not in self.coverred_objects:
                coverred_objects.add(key)
        return coverred_objects

    def find_most_uncovered_tc(self):
        most_uncovered_tc = []
        max_uncovered_objects = 0
        max_uncovered_tc_index = []
        for tc, i in zip(self.testsuite.test_cases, range(len(self.testsuite.test_cases))):
            if tc in self.ordered_test_cases:
                continue
            count = len(self.get_covering_objects(tc))
            if count > max_uncovered_objects:
                max_uncovered_objects = count
                most_uncovered_tc = [tc]
                max_uncovered_tc_index = [i]
            elif count == max_uncovered_objects:
                most_uncovered_tc.append(tc)
                max_uncovered_tc_index.append(i)
        return most_uncovered_tc, max_uncovered_tc_index
            
    def optimize(self):
        no_interacting_test_cases = []
        no_interacting_test_cases_indices = []
        for tc, i in zip(self.testsuite.test_cases, range(len(self.testsuite.test_cases))):
            if len(tc.interactions) == 0 or len(tc.states) == 0:
                no_interacting_test_cases.append(tc)
                no_interacting_test_cases_indices.append(i)

        while len(self.ordered_test_cases) < len(self.testsuite.test_cases) - len(no_interacting_test_cases):
            next_test_cases, tc_indices = self.find_most_uncovered_tc()
            next_test_case = random.choice(next_test_cases)
            tc_index = tc_indices[next_test_cases.index(next_test_case)]
            self.ordered_test_cases.append(next_test_case)
            self.ordering.append(tc_index)
            coverred_objects = self.get_covering_objects(next_test_case)
            self.coverred_objects = self.coverred_objects.union(coverred_objects)
        self.ordered_test_cases.extend(no_interacting_test_cases)
        self.ordering.extend(no_interacting_test_cases_indices)
        return self.ordered_test_cases, self.ordering
    

if __name__ == "__main__":
    files = os.listdir("data/test_suite")
    files = [file for file in files if file.endswith(".json")]
    prefix = "with-sibling-segmentation-"
    for file in files:
        file = os.path.join("data/test_suite", file)
            # create folder if not exist
        folder_name = file.replace(".json", "").split("fraggen")[1]
        folder_name = prefix + folder_name
        folder_name = os.path.join("data/test_suite", folder_name)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        export_file = os.path.join(folder_name, "greedy_segment_solutions.json")

        print("Processing file: ", file)
        test_suite = parse_test_suite_from_file(file)
        print("Test suite: ", len(test_suite.test_cases))
        optimizer = GreedyObjectsOptimizer(test_suite)
        ordered_tests, orderings = optimizer.optimize()
        # print("Ordered tests: ", orderings)
        apfd = APFD(orderings, test_suite)
        print("APFD: ", apfd)
        solution = {
            "mask": orderings,
            "statuses": [test_suite.test_cases[i].status for i in orderings],
            "APFD": apfd
        }

        with open(export_file, "w") as f:
            json.dump(solution, f, indent=2)


