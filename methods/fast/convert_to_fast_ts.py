import json
import os
import pickle

def read_json(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

def get_all_test_object(json_data):
    tobjs = set()
    for tc in json_data:
        for interaction, state, i in zip(tc["interactions"], tc["states"], range(len(tc["interactions"]))):
            tobjs.add((interaction["test_object"]["id"], state["url"]))
        # for interaction in tc["interactions"]:
        #     tobjs.add(interaction["test_object"]["id"])
    return tobjs

def conver_to_matrix(json_data):
    # json_data = mark_id(json_data)
    tobjs = get_all_test_object(json_data)
    matrix = []
    for tc in json_data:
        row = []
        for tobj,i in zip(tobjs, range(len(tobjs))):
            # if tobj in [x["test_object"]["id"] for x in tc["interactions"]]:
            #     row.append("1")
            if tobj in [(to["test_object"]["id"], ts["url"]) for to, ts in zip(tc["interactions"], tc["states"])]:
                row.append(i+1)
        matrix.append(row)
    return matrix, tobjs

def mark_id(json_data):
    id = 0
    for tc in json_data:
        for interaction, state, i in zip(tc["interactions"], tc["states"], range(len(tc["interactions"]))):
            interaction["test_object"]["id"] = id
            state["id"] = id
            id += 1
    return json_data

def write_matrix(matrix, tobjs, file_path):
    with open(file_path, "w") as f:
        for i in range(len(matrix)):
            f.write(" ".join([str(x) for x in matrix[i]]) + "\n")

def get_fault_matrix(json_data):
    # fault matrix is a dict, key is tcID, value is list of faults
    fault_matrix = {}
    for tc, i in zip(json_data, range(len(json_data))):
        failures = tc.get("failures", [])
        if len(failures) > 0:
            fault_matrix[i+1] = []
            for fault in failures:
                fault_matrix[i+1].append(fault)
    return fault_matrix

if __name__ == "__main__":
    unprocessed_folder = "my_input/test_suites"
    json_files = os.listdir(unprocessed_folder)
    processed_folder = "my_input/processed_test_suites"
    if not os.path.exists(processed_folder):
        os.mkdir(processed_folder)
    processed_files = {

    }
    for json_file in json_files:
        json_file = os.path.join(unprocessed_folder, json_file)
        subfolder = os.path.join(processed_folder, os.path.basename(json_file).split("_")[0].replace(".json", ""))
        
        if not os.path.exists(subfolder):
            os.mkdir(subfolder)
        else:
            i = 1
            while os.path.exists(subfolder + "_v{}".format(i)):
                i += 1
            subfolder = subfolder + "_v{}".format(i)
            os.mkdir(subfolder)

        out_matrix_file = json_file.replace(".json", ".txt").replace("json", "matrix").replace(unprocessed_folder, processed_folder)
        out_matrix_file = os.path.join(subfolder, os.path.basename(out_matrix_file))
        json_data = read_json(json_file)
        matrix, tobjs = conver_to_matrix(json_data)
        write_matrix(matrix, tobjs, out_matrix_file)
        fault_matrix = get_fault_matrix(json_data)
        fault_matrix_file = "fault_matrix_key_tc.pickle"
        fault_matrix_file = os.path.join(subfolder, fault_matrix_file)
        pickle.dump(fault_matrix, open(fault_matrix_file, "wb"))
        processed_files[json_file] = {
            "matrix": out_matrix_file,
            "fault_matrix": fault_matrix_file
        }

    with open("my_input/processed_files.json", "w") as f:
        json.dump(processed_files, f, indent=4)
    
