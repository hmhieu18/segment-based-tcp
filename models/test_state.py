import json
import subprocess
import json_fix
import os
from .segmentator.DOMParser import DOMParser

def get_segmentation_of_html_cli(html):
    #write html to file
    abs_path = os.path.abspath(os.path.dirname(__file__))
    html_path = os.path.join(abs_path, "tmp.html")
    with open(html_path, "w") as f:
        f.write(html)

    #run segmentation
    segmentatorPath = "/Users/hieu.huynh/Documents/Projects/web-segmentation/DOM-Tree-Comparison/Implementation/DOM-Trees-Comparator/segment_cli.py"
    python3_ = "/usr/local/bin/python3"
    cmd = f"{python3_} {segmentatorPath} -f {html_path}"
    #execute command and get the output
    try:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode("utf-8")
        # print(output)
        #get last line of output
        lines = output.split("\n")
        last_line = lines[-2]
        data = json.loads(last_line)

        segments = data['xpaths']
        siblings = data['siblings']
    
    except Exception as e:
        print("Error", e)
        segments = []
        siblings = []
    return segments, siblings

def get_segmentation_of_html(file_path, driver):
    url = "file://" + file_path
    print("Processing: ", url)
    print("Driver: ", driver)
    dom_document = DOMParser(url, driver=driver, killDriver=False)
    driver = dom_document.browser
    result = dom_document.get_segments()
    segments = result['xpaths']
    siblings = result['siblings']
    return segments, siblings, driver


class State:
    driver = None
    def __init__(self, id, url, name, success, identical, segments=[], traceState=None, siblings=[], fault_type="", fault_des="", ref_step="") -> None:
        self.id = id
        self.url = url
        self.name = name
        self.success = success
        self.identical = identical
        self.segments = segments
        self.traceState = traceState
        self.siblings = siblings
        self.fault_type = fault_type
        self.fault_description = fault_des
        self.ref_step = ref_step


    def from_json(json, diffs, segment_dict={}, filename=None, need_segment = True):
        if json['id'] in segment_dict:
            return State(json['id'], json['url'], json['name'], json['success'], json['identical'], segment_dict[json['id']]["segments"], json['traceState'], segment_dict[json['id']]["siblings"], State.get_html_file_name(json, filename))
        
        state_name = json['name']
        for diff in diffs:
            if diff['state'] == state_name:
                html_file_name = State.get_html_file_name(json, filename)
                if html_file_name is None:
                    continue
                segments, siblings, State.driver = get_segmentation_of_html(html_file_name, State.driver) if need_segment else ([], [], State.driver)
                return State(json['id'], json['url'], json['name'], json['success'], json['identical'], segments, json['traceState'], siblings, html_file_name)
        return State(json['id'], json['url'], json['name'], json['success'], json['identical'], [], json['traceState'], [], State.get_html_file_name(json, filename))

    def get_html_file_name(json, filename):
        traceState = json['traceState']
        html_file_name = f"frag_state{traceState}.html"

        directory = os.path.dirname(filename)
        html_path = os.path.join(directory, "doms", html_file_name)
        if not os.path.exists(html_path):
            html_file_name = f"state{traceState}.html"
            #get directory of the filename
            directory = os.path.dirname(filename)
            html_path = os.path.join(directory, "doms", html_file_name)
        if not os.path.exists(html_path):
            print("Cannot find html file of state", traceState)
            return None
        return html_path

    def from_generated_json(json):
        id = json.get('id', "")
        url = json.get('url', "")
        name = json.get('name', "")
        success = json.get('success', False)
        identical = json.get('identical', False)
        segments = json.get('segments', [])
        traceState = json.get('traceState', "")
        siblings = json.get('siblings', [])
        fault_type = json.get('fault_type', "")
        fault_description = json.get('fault_description', "")
        ref_step = json.get("ref_step", "")
        return State(id, url, name, success, identical, segments, traceState, siblings, fault_type, fault_description, ref_step)
        # return State(json['id'], json['url'], json['name'], json['success'], json['identical'], json['segments'], json['traceState'], json['siblings'], json['fault_type'], json['fault_description'], json.get("ref_step", ""))
    
    def __str__(self) -> str:
        return f"State: {self.id} {self.url} {self.name} {self.success} {self.identical} {self.segments} {self.traceState}"
    
    def __json__(self):
        return {
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "success": self.success,
            "identical": self.identical,
            "segments": self.segments,
            "traceState": self.traceState,
            "siblings": self.siblings
        }
    
    def __del__(self):
        if State.driver is not None:
            State.driver.close()
            State.driver = None