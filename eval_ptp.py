import json
import time
import numpy as np
import random


import os
import sys

import pandas as pd
import numpy as np
from evaluation_utils import APFD, APFDc, APSD, APOD, APOTD, APSBD, fault_coverage, segment_coverage, object_coverage, object_type_coverage, sibling_coverage
from models.test_suite import TestSuite
from ranker_object import TestCaseRankerObject
from terminator import Terminator
# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite

def get_solution_object(order, testsuite):
    solution_object = {}
    # solution_object["mask"] = order
    # solution_object["statuses"] = [1 if len(testsuite.test_cases[i].failures) == 0 else 0
    #                            for i in order]
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
    return solution_object

def export_solutions_csv(solutions, file_name):
    df = pd.DataFrame.from_dict(solutions, orient="index")
    df = df.drop(columns=["mask"])
    #set index name
    df.index.name = "solution"
    #add average column to the end as the average of apsd, apod, apotd, apsbd
    df["average"] = df[["APSD", "APOD", "APOTD", "APSBD"]].mean(axis=1)
    df.to_csv(file_name)

def get_solutions(json_file, testsuite, target_project):
    solutions = {}
    json_data = None
    with open(json_file, "r") as f:
        json_data = json.load(f)
        solutions = {}
        for method in json_data:
            if target_project in method["file"]:
                sequences = method["sequence"]
                
                method["APFDs"] = []
                method["APFDCs"] = []
                method["APSDs"] = []
                method["APODs"] = []
                method["APOTDs"] = []
                method["APSBDs"] = []

                sum_apfd, sum_apfdc, sum_apsd, sum_apod, sum_apotd, sum_apsbd = 0, 0, 0, 0, 0, 0
                for sequence in sequences:
                    solution = get_solution_object(sequence, testsuite)
                    
                    method["APFDs"].append(solution["APFD"])
                    method["APFDCs"].append(solution["APFDC"])
                    method["APSDs"].append(solution["APSD"])
                    method["APODs"].append(solution["APOD"])
                    method["APOTDs"].append(solution["APOTD"])
                    method["APSBDs"].append(solution["APSBD"])

                    sum_apfd += solution["APFD"]
                    sum_apfdc += solution["APFDC"]
                    sum_apsd += solution["APSD"]
                    sum_apod += solution["APOD"]
                    sum_apotd += solution["APOTD"]
                    sum_apsbd += solution["APSBD"]
                solutions[method["method"]] = {
                    "mask": [],
                    "APFD": sum_apfd / len(sequences),
                    "APFDC": sum_apfdc / len(sequences),
                    "APSD": sum_apsd / len(sequences),
                    "APOD": sum_apod / len(sequences),
                    "APOTD": sum_apotd / len(sequences),
                    "APSBD": sum_apsbd / len(sequences),
                }
        if len(solutions) == 0:
            input("No solution found for " + target_project)
    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=2)
    return solutions

if __name__ == "__main__":
    files = os.listdir("data/test_suite_annotated")
    files = [file for file in files if file.endswith(".json")]

    processed_files = []
    apfds = []
    apfdcs = []
    apsds = []
    apods = []
    apotds = []
    apsbds = []
    cur_time = time.time()
    ptp_solution = "/Users/hieu.huynh/Documents/prioritization/annotate-data/data/results_fast_mul.json"
    for file in files:
        # if "mattermost_221" not in file:
        #     continue
        print("Processing", file)
        
        file = os.path.join(f"data/test_suite_annotated", file)
        folder_name = file.replace(".json", "").replace("data/test_suite_annotated", f"data/test_suite_annotated/solutions-{cur_time}")
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        test_suite = parse_test_suite_from_file(file)

        export_file = os.path.join(folder_name, "all_solutions.json")
        
        solutions = get_solutions(ptp_solution, test_suite, os.path.basename(file))
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
