import json
import hashlib
import pandas as pd
import os
import cv2


def get_representative_state(hash_states, state_name):
    for hash_state in hash_states:
        if state_name in hash_states[hash_state]:
            return hash_state
    return None

def get_urls(methodResults):
    states = methodResults["crawlStates"]
    urls = []
    for state in states:
        urls.append(state["url"])
    return sorted(list(set(urls)))

def write_urls_to_excel(urls, writer):
    df = pd.DataFrame(urls, columns=["URL"])
    df.to_excel(writer, sheet_name='urls', index=False)
    writer.book.add_worksheet('groups')
    # writer._save()


if __name__ == "__main__":
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/claroline/test-results_rhel/claroline/claroline_DOM_RTED_0.00517361_60mins/localhost/crawl0/test-results/1/testRun.json"
    json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/petclinic/test-results_rhel/petclinic/petclinic_DOM_RTED_0.005075607_60mins/localhost/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/phoenix/test-results_rhel/phoenix/phoenix_DOM_RTED_0.0774_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file = "sample.json"
    json_data = json.load(open(json_file, "r"))
    methods = json_data.keys()
    hash_old_states = {}
    hash_new_states = {}
    compared_states = []
    urls = []
    folder = os.path.dirname(json_file)
    excel_file = os.path.join(folder, os.path.basename(
        json_file).replace(".json", ".xlsx"))
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df = pd.DataFrame(columns=["method", "old_state", "new_state",
                      "old_state_name", "new_state_name", "old_state_hash", "new_state_hash"])
    line_count = 1
    image_cells = {}
    for method in methods:
        try:
            duration = json_data[method]["duration"]
            testSrcPath = json_data[method]["testSrcPath"]
            testStatus = json_data[method]["testStatus"]
            diffs = json_data[method]["diffs"]
            failureMessage = json_data[method]["failureMessage"]
            methodResult = json_data[method]["methodResult"]
            urls += get_urls(methodResult)

            if len(diffs) % 2 != 0:
                print("Error")
                input("Press Enter to continue...")
                continue
            for i in range(0, len(diffs), 2):
                old_state_html = diffs[i]["oldState"]
                new_state_html = diffs[i]["newState"]

                old_state_name = diffs[i+1]["oldState"]
                new_state_name = diffs[i+1]["newState"]


                old_state_hash = get_representative_state(hash_states=hash_old_states, state_name=old_state_name) 
                if old_state_hash is None:
                    old_state_hash = hashlib.md5(
                        old_state_html.encode('utf-8').strip()).hexdigest()
                
                new_state_hash = get_representative_state(hash_states=hash_new_states, state_name=new_state_name)
                if new_state_hash is None:
                    new_state_hash = hashlib.md5(
                        new_state_html.encode('utf-8').strip()).hexdigest()

                if old_state_hash not in hash_old_states:
                    hash_old_states[old_state_hash] = []

                if old_state_name not in hash_old_states[old_state_hash]:
                    hash_old_states[old_state_hash].append(old_state_name)

                if new_state_hash not in hash_new_states:
                    hash_new_states[new_state_hash] = []

                if new_state_name not in hash_new_states[new_state_hash]:
                    hash_new_states[new_state_hash].append(new_state_name)

                old_png_file = os.path.join(
                    folder, method, "diffs", old_state_name)
                new_png_file = os.path.join(
                    folder, method, "diffs", new_state_name)
                if old_state_hash != new_state_hash and (old_state_hash, new_state_hash) not in compared_states:
                    df = df._append({"method": method, "old_state": "", "new_state": "", "old_state_name": old_state_name,
                                    "new_state_name": new_state_name, "old_state_hash": old_state_hash, "new_state_hash": new_state_hash, "added": "", "deleted": "", "modified": ""
                                    }, ignore_index=True)
                    line_count += 1
                    old_state_cell = "B" + str(line_count)
                    image_cells[old_state_cell] = old_png_file
                    new_state_cell = "C" + str(line_count)
                    image_cells[new_state_cell] = new_png_file
                compared_states.append((old_state_hash, new_state_hash))
        except Exception as e:
            print("Error", e)
            continue
        
    df.to_excel(writer, sheet_name='difference_annotation', index=False)

    count = 0
    for hash_state in hash_old_states:
        if len(hash_old_states[hash_state]) > 1:
            count += 1
            print(hash_old_states[hash_state])

    print("count: ", count)

    count = 0
    for hash_state in hash_new_states:
        if len(hash_new_states[hash_state]) > 1:
            count += 1
            print(hash_state, hash_new_states[hash_state])

    print("count: ", count)


    workbook = writer.book
    worksheet = writer.sheets['difference_annotation']
    for cell in image_cells:
        width, height = cv2.imread(image_cells[cell]).shape[:2]
        scaled_width = width * 0.4
        scaled_height = height * 0.4
        worksheet.insert_image(cell, image_cells[cell], {
                               "x_scale": 0.4, "y_scale": 0.4})
        row = int(cell[1:])-1
        worksheet.set_row_pixels(row, scaled_height)
        col = cell[0]
        col = ord(col) - ord('A')
        worksheet.set_column_pixels(col, col, scaled_width)

    writer.book.add_worksheet('urls')
    urls = sorted(list(set(urls)))
    write_urls_to_excel(urls, writer)
    
    writer._save()