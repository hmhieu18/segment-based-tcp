import json
import hashlib
import pandas as pd
import os
import cv2
from PIL import Image
import Levenshtein

def compare_htmls(html1, html2):
    # compare two htmls by levenshtein distance
    percent = Levenshtein.distance(html1, html2) / max(len(html1), len(html2))
    return percent

def get_representative_state(hash_states, state_name):
    for hash_state in hash_states:
        if state_name in hash_states[hash_state]:
            return hash_state
    return None


def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()


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


def get_width_height(image_path):
    # get width and height of image without loading it into memory
    img_x = Image.open(image_path)._getexif()[40962]
    img_y = Image.open(image_path)._getexif()[40963]
    return img_x, img_y

def find_closest_state(html, compared_states, element_type, element_text, element_attrs):
    threshold = 0.1
    min_distance = 1
    closest_state = None
    if html == "":
        return closest_state
    for hash_state in compared_states:
        if element_type in hash_state and element_text in hash_state and element_attrs in hash_state:
            distance = compare_htmls(html, compared_states[hash_state][1])
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_state = hash_state
    return closest_state

def get_html_hash(diffs):
    state_html = ""
    state_png_name = ""
    state_old_png_name = ""
    state_png_path = ""
    state_old_png_path = ""
    comp_result = ""
    for diff in diffs:
        if diff["state"] == state_name and diff["newState"].lower().startswith("<html"):
            state_html = diff["newState"]
            comp_result = diff.get("compResult", "")
        if diff["state"] == state_name and diff["newState"].lower().endswith(".png"):
            state_png_name = diff["newState"]
            state_png_path = os.path.join(
                folder, method, "diffs", state_png_name)
            comp_result = diff.get("compResult", "")
            if not os.path.exists(state_png_path):
                state_png_path = os.path.join(
                    folder, state_png_name)
                
        if diff["state"] == state_name and diff["oldState"].lower().endswith(".png"):
            state_old_png_name = diff["oldState"]
            state_old_png_path = os.path.join(
                folder, method, "diffs", state_old_png_name)
            if not os.path.exists(state_old_png_path):
                state_old_png_path = os.path.join(
                    folder, state_old_png_name)
            
    if state_html == "":
        state_html_name = os.path.basename(
            state_png_name).replace(".png", ".html")
        state_html_path = os.path.join(folder, "doms", state_html_name)
        if os.path.exists(state_html_path) and os.path.isfile(state_html_path):
            state_html = read_file(state_html_path)
    state_hash = hashlib.md5(
        state_html.encode('utf-8').strip()).hexdigest()
    return state_hash, state_html, state_png_path, state_old_png_path, comp_result

if __name__ == "__main__":
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/claroline/test-results_rhel/claroline/claroline_DOM_RTED_0.00517361_60mins/localhost/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/addressbook/test-results_rhel/addressbook/addressbook_HYBRID_0.0_60mins/localhost/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/dimeshift/test-results_rhel/dimeshift/dimeshift_HYBRID_0.0_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file= "/Users/hieu.huynh/Downloads/dataset-fraggen/ppma/test-results_rhel/ppma/ppma_HYBRID_0.0_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/pagekit/test-results_rhel/pagekit/pagekit_HYBRID_0.0_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/dimeshift/test-results_mac/dimeshift/dimeshift_VISUAL_HYST_6357.869868220296_60mins/192.168.99.101/crawl0/test-results/0/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/claroline/test-results_rhel/claroline/claroline_DOM_RTED_0.00517361_60mins/localhost/crawl0/test-results/0/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/petclinic/test-results_mac/petclinic/petclinic_VISUAL_HYST_1724.088930986449_60mins/localhost/crawl0/test-results/0/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/claroline/test-results_rhel/claroline/claroline_HYBRID_0.0_60mins/localhost/crawl0/test-results/1/testRun.json"
    json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/addressbook/test-results_mac/addressbook/addressbook_HYBRID_0.0_60mins/localhost/crawl0/test-results/0/testRun_mut.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/petclinic/test-results_rhel/petclinic/petclinic_DOM_RTED_0.005075607_60mins/localhost/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/mantisbt/test-results_rhel/mantisbt/mantisbt_HYBRID_0.0_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file = "/Users/hieu.huynh/Downloads/dataset-fraggen/phoenix/test-results_rhel/phoenix/phoenix_DOM_RTED_0.0774_60mins/192.168.99.101/crawl0/test-results/1/testRun.json"
    # json_file = "sample.json"
    json_data = json.load(open(json_file, "r"))
    methods = json_data.keys()
    hash_old_states = {}
    hash_new_states = {}
    compared_states = {}
    urls = []
    folder = os.path.dirname(json_file)
    excel_file = os.path.join(folder, os.path.basename(
        json_file).replace(".json", ".xlsx"))
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df = pd.DataFrame(columns=["method", "new_state_name", "new_html_hash","old_state_image", "new_state_image", "compResult",
                      "step", "step_name", "fault_type", "fault_type_", "revised_result", "revised_result_", "filter_result", "result", "current_url", "action", "element_xpath", "element_type", "element_text", "element_attrs", "ref_step"])
    line_count = 2
    image_cells = {}
    for method in methods:
        duration = json_data[method]["duration"]
        testSrcPath = json_data[method]["testSrcPath"]
        testStatus = json_data[method]["testStatus"]
        diffs = json_data[method]["diffs"]
        failureMessage = json_data[method]["failureMessage"]
        methodResult = json_data[method]["methodResult"]
        urls += get_urls(methodResult)
        states = methodResult["crawlStates"]
        crawl_paths = methodResult["crawlPath"]
        for i in range(len(crawl_paths)):
            state = states[i]
            crawl_path = crawl_paths[i]
            current_url = state["url"]
            state_name = state["name"]
            state_hash, state_html, state_png_path, state_old_png_path, comp_result = get_html_hash(diffs)

            action = crawl_path["eventable"]["eventType"]
            element_xpath = crawl_path["eventable"]["identification"]["value"]
            element_type = crawl_path["eventable"]["element"]["tag"]
            element_text = crawl_path["eventable"]["element"]["text"]
            element_attrs = crawl_path["eventable"]["element"]["attributes"]
            ref_step = ""
            key = (state_hash, element_type, element_text, json.dumps(element_attrs))
            print("state_name", state_name)
            closest_key = find_closest_state(state_html, compared_states, element_type, element_text, json.dumps(element_attrs))
            if closest_key is None:
                compared_states[key] = (method + "_step_" + str(i), state_html)
                ref_step = ""
            else:
                ref_step = compared_states[closest_key][0]
            # print("ref_step", ref_step)
            # input()
            
            step_name = method + "_step_" + str(i)
            # fault type formula: =IF(ISBLANK(fault_type_),VLOOKUP(ref_step,H:J, 3, FALSE),fault_type_)
            fault_type = f'=IF(ISBLANK(J{line_count}),VLOOKUP(U{line_count},H:J, 3, FALSE),J{line_count})'
            fault_type_ = ""
            revised_result = f'=IF(ISBLANK(L{line_count}),VLOOKUP(U{line_count},H:L, 5, FALSE),L{line_count})'
            revised_result_ = ""
            # filter result formula: =IF(A2=A3,IF(OR(J3="F", J2="F"),"F","T"),J2)
            filter_result = f'=IF(A{line_count}=A{line_count+1},IF(OR(K{line_count+1}="F", K{line_count}="F"),"F","T"),K{line_count})'
            result = crawl_path["success"]
            df = df._append({"method": method, "new_state_name": state_name, "new_html_hash": state_hash, "step": i, "result": result, "current_url": current_url, "action": action, "compResult": comp_result,
                            "element_xpath": element_xpath, "element_type": element_type, "element_text": element_text, "element_attrs": element_attrs, "fault_type": fault_type, "ref_step": ref_step, "step_name": step_name, "fault_type_": fault_type_, "revised_result": revised_result, "revised_result_": revised_result_, "filter_result": filter_result
                            }, ignore_index=True)
            if state_png_path != "":
                image_cells["E" + str(line_count)] = state_png_path
            if state_old_png_path != "":
                image_cells["D" + str(line_count)] = state_old_png_path
            line_count += 1

        if len(states) > len(crawl_paths):
            state = states[-1]
            current_url = state["url"]
            state_name = state["name"]
            state_hash, state_html, state_png_path, state_old_png_path, comp_result = get_html_hash(diffs)
            action = ""
            element_xpath = ""
            element_type = ""
            element_text = ""
            element_attrs = ""
            ref_step = ""
            step_name = method + "_step_" + str(i)
            fault_type = f'=IF(ISBLANK(J{line_count}),VLOOKUP(U{line_count},H:J, 2, FALSE),J{line_count})'
            fault_type_ = ""
            revised_result = f'=IF(ISBLANK(L{line_count}),VLOOKUP(U{line_count},H:L, 4, FALSE),L{line_count})'
            revised_result_ = ""
            filter_result = f'=IF(A{line_count}=A{line_count+1},IF(OR(K{line_count+1}="F", K{line_count}="F"),"F","T"),K{line_count})'
            key = (state_hash, element_type, element_text, json.dumps(element_attrs))
            closest_key = find_closest_state(state_html, compared_states, element_type, element_text, json.dumps(element_attrs))
            print("state_name", state_name)
            # input(closest_key)
            if closest_key is None:
                compared_states[key] = (method + "_step_" + str(i), state_html)
                ref_step = ""
            else:
                ref_step = compared_states[closest_key][0]
            result = True
            df = df._append({"method": method, "new_state_name": state_name, "new_html_hash": state_hash, "step": len(crawl_paths), "result": result, "current_url": current_url, "action": action, "compResult": comp_result,
                            "element_xpath": element_xpath, "element_type": element_type, "element_text": element_text, "element_attrs": element_attrs, "fault_type": fault_type, "ref_step": ref_step, "step_name": step_name, "fault_type_": fault_type_, "revised_result": revised_result, "revised_result_": revised_result_, "filter_result": filter_result
                            }, ignore_index=True)
            if state_png_path != "":
                image_cells["E" + str(line_count)] = state_png_path
            if state_old_png_path != "":
                image_cells["D" + str(line_count)] = state_old_png_path
            line_count += 1

    df.to_excel(writer, sheet_name='difference_annotation', index=False)

    workbook = writer.book
    worksheet = writer.sheets['difference_annotation']
    for cell in image_cells:
        width, height = cv2.imread(image_cells[cell]).shape[:2]
        scaled_width = width * 0.1
        scaled_height = height * 0.25
        worksheet.insert_image(cell, image_cells[cell], {
                               "x_scale": 0.4, "y_scale": 0.4})
        row = int(cell[1:])-1
        worksheet.set_row(row, scaled_height)
        col = cell[0]
        col = ord(col) - ord('A')
        worksheet.set_column(col, col, scaled_width)

    # create new sheet for urls
    writer.book.add_worksheet('file_original')
    # write folder name to file_original
    df1 = pd.DataFrame([folder], columns=["folder"])
    df1.to_excel(writer, sheet_name='file_original', index=False)
    writer._save()
