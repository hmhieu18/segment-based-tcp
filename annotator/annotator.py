import sys
import os
import json
import random
from models.test_suite import TestSuite
import pandas as pd
import hashlib

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

def urls_to_excel(urls, file_name):
    if os.path.exists(file_name):
        return
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df = pd.DataFrame(urls, columns=["URL"])
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.book.add_worksheet('groups')
    writer._save()

def read_urls_groups_from_excel(file_name):
    df = pd.read_excel(file_name, sheet_name='groups')
    #group names is the header of columns
    group_names = df.columns.values.tolist()
    dict = {}
    for group_name in group_names:
        urls = df[group_name].tolist()
        urls = [url for url in urls if str(url) != 'nan']
        dict[group_name] = urls
    return dict

def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite

def get_hash_file(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

if __name__ == "__main__":
    files = os.listdir("data/test_suite")
    files = [file for file in files if file.endswith(".json")]
    
    for file in files:
        if "_Users_hieu.huynh_Downloads_dataset-fraggen_phoenix_test-results_rhel_phoenix_phoenix_DOM_RTED_0.0774_60mins_192.168.99.101_crawl0_test-results_0_testRun.json" not in file:
            continue
        print("Current file", file)
        file = os.path.join("data/test_suite", file)

        test_suite = parse_test_suite_from_file(file)


        # urls = test_suite.get_crawl_urls()
        # urls = sorted(urls)
        # print("Total urls", urls)
        # excel_file = file.replace(".json", ".xlsx")
        # urls_to_excel(urls, excel_file)
        # #open the excel file
        # os.system("open " + excel_file)
        # input("Press Enter to continue...")
        # urls_groups = read_urls_groups_from_excel(excel_file)
        # print("Total groups", urls_groups)

        states = test_suite.get_all_states()
        print(len(states))

