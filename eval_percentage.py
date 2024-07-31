import json
import os
import pandas as pd
from ranker_revised import parse_test_suite_from_file
from methods.evaluation_utils import percentage_of_test_case_for_100_fault_coverage

# Define paths
root_folder = "/Users/hieu.huynh/Documents/prioritization/segment-based-tcp-new/data/solutions/solutions-main-p"
json_folder = "data/test_suite_annotated"

# List folders and corresponding JSON files
folders = [folder for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, folder))]
json_files = [os.path.join(json_folder, f"{folder}.json") for folder in folders]

# Process each folder and corresponding JSON file
for folder, json_file in zip(folders, json_files):
    solution_file = os.path.join(root_folder, folder, "all_solutions.json")
    solution_csv_file = os.path.join(root_folder, folder, "all_solutions.csv")

    # Load solutions from JSON file
    with open(solution_file, "r") as f:
        solutions = json.load(f)
    
    # Parse test suite from JSON file
    test_suite = parse_test_suite_from_file(json_file)
    
    # Compute percentage for 100% fault coverage
    for solution in solutions:
        ordered_fault_dict, last_fault_covered_test_case, len_ts = percentage_of_test_case_for_100_fault_coverage(
            solution[1]["mask"], test_suite
        )
        solution[1]["percentage_for_100_coverage"] = (last_fault_covered_test_case + 1) / len_ts

    # Save updated solutions back to JSON file
    with open(solution_file, "w") as f:
        json.dump(solutions, f, indent=4)

    # Load CSV file
    df = pd.read_csv(solution_csv_file)
    
    # Add new column to DataFrame
    df['percentage_for_100_coverage'] = [solution[1]["percentage_for_100_coverage"] for solution in solutions]
    
    # Save updated DataFrame to CSV file
    df.to_csv(solution_csv_file, index=False)
