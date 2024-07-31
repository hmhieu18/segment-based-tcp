import json
import time
import numpy as np
import random


import os
import sys

import pandas as pd
import numpy as np
from models.test_suite import TestSuite
# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite

def export_analysis(test_suite, writer, project_name):
    df = pd.DataFrame()
    failures = {}
    for tc in test_suite:
        failure = tc.failures[0] if len(tc.failures) > 0 else ""
        if failure != "":
            if failure not in failures:
                failures[failure] = 1
            else:
                failures[failure] += 1
        tc_obj = {
            "test_case": tc.id,
            "states": len(tc.states),
            "interations": len(tc.interactions),
            "status": True if len(tc.failures) == 0 else False,
            "duration": tc.duration,
            "failure": failure,
        }
        for f in tc.failures:
            tc_obj[f] = True
        df = df._append(tc_obj, ignore_index=True)
    
    number_of_test_cases = len(test_suite)
    number_of_states = sum([len(tc.states) for tc in test_suite])
    number_of_success_test_cases = len([tc for tc in test_suite if len(tc.failures) == 0])
    number_of_failed_test_cases = len([tc for tc in test_suite if len(tc.failures) > 0])
    number_of_failures = len(failures)


    # write in the top of the file, using excelwriter
    #write the data
    #get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    #if the sheet already exist
    if project_name in workbook.sheetnames:
        worksheet = workbook.get_worksheet_by_name(project_name)
    else:
        worksheet = workbook.add_worksheet(project_name)
    #write the data
    #insert 5 rows at the top
    worksheet.write(0, 0, f"Number of test cases")
    worksheet.write(0, 1, number_of_test_cases)
    worksheet.write(1, 0, f"Number of states")
    worksheet.write(1, 1, number_of_states)
    worksheet.write(2, 0, f"Number of success test cases")
    worksheet.write(2, 1, number_of_success_test_cases)
    worksheet.write(2, 2, number_of_success_test_cases/number_of_test_cases)
    worksheet.write(3, 0, f"Number of failed test cases")
    worksheet.write(3, 1, number_of_failed_test_cases)
    worksheet.write(4, 0, f"Number of failures")
    worksheet.write(4, 1, number_of_failures)
    for failure, count, i in zip(failures.keys(), failures.values(), range(len(failures))):
        worksheet.write(5+i, 0, failure)
        worksheet.write(5+i, 1, count)

    df.to_excel(writer, sheet_name=project_name, startrow=5+len(failures))
    obj = {
        "Number of test cases": number_of_test_cases,
        "Number of states": number_of_states,
        "Number of success test cases": number_of_success_test_cases,
        "Number of failed test cases": number_of_failed_test_cases,
        "Number of failures": number_of_failures,
        "Failures": failures
    }
    return df, obj


def merge_solution_file(sol_file, writer):
    #add all sheet in excel sol_file to writer
    df = pd.read_excel(sol_file, sheet_name=None)
    for sheet_name in df.keys():
        # keep rows that have solution is not an integer
        df[sheet_name] = df[sheet_name][~df[sheet_name]["solution"].astype(str).str.isdigit()]
        df[sheet_name].to_excel(writer, sheet_name=sheet_name)
    #sort sheets by name
    workbook = writer.book
    sheets = workbook.worksheets()
    sheets.sort(key=lambda x: x.name)

def get_analyze_dfs(writer):
    files = os.listdir("data/test_suite_annotated")
    files = [file for file in files if file.endswith(".json")]
    dfs = []
    objs = {}
    for file in files:
        print("Processing", file)
        project_name = os.path.basename(file).split("/")[-1]
        test_suite = parse_test_suite_from_file(os.path.join("data/test_suite_annotated", file))
        df, obj = export_analysis(test_suite, writer, project_name)
        dfs.append(df)
        objs[project_name] = obj
    # merge objs to one df
    df = pd.DataFrame.from_dict(objs)
    # export to excel
    df.to_excel(writer, sheet_name="summary")
    return dfs


if __name__ == "__main__":
    files = os.listdir("data/test_suite_annotated")
    files = [file for file in files if file.endswith(".json")]
    files.sort()
    excel_file = "data/test_suite_analysis.xlsx"
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    objs = {}
    for file in files:
        print("Processing", file)
        project_name = os.path.basename(file).split("/")[-1].replace("6_nov", "").replace("3_nov", "").replace(".json", "")
        if "_test-results" in project_name:
            project_name = project_name.split("_test-results")[0]
        test_suite = parse_test_suite_from_file(os.path.join("data/test_suite_annotated", file))
        df, obj = export_analysis(test_suite, writer, project_name)
        objs[project_name] = obj
    # merge objs to one df
    df = pd.DataFrame.from_dict(objs)
    df = df.transpose()
    # export to excel
    df.to_excel(writer, sheet_name="summary")
    # merge_solution_file("data/test_suite_annotated/solutions-1695904077.2750971/merged_std.xlsx", writer)
    writer._save()


        
