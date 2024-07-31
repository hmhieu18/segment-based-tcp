import os
import json
import time
from urllib.parse import urlparse
from datetime import datetime
from selenium import webdriver
from .DomNode import DomNode
from .DomBlock import DomBlock

from .Segmentor import *
from .visualizer import *

from .segActions import *


class DOMParser:
    def __init__(self, urlStr, precomputed_dir="", upper_bound=None, page_height=1080, page_width=192, driver=None, killDriver=True):
        self.url = None
        self.fileName = None
        self.browser = None
        self.domOut = None
        self.imgOut = None
        self.html = None
        self.page_height = 0
        self.page_width = 0
        self.root_node = None
        self.nodeList = []
        self.segments = None
        self.max_level = 0
        self.upper_bound = upper_bound
        self.page_height = page_height
        self.page_width = page_width
        if precomputed_dir == "":
            self.setUrl(urlStr)
            self.setDriver(driver=driver)
            self.getWebPage()
            self.getScreenshot()
            self.getDomTree()
        else:
            self.load_precomputed(precomputed_dir)

        time_flag_1 = time.time()
        save_subtree_depth(self.root_node)
        self.segment()
        # self.get_segmentation_layout()
        self.optimize_segmentation_layout()
        # self.get_sheeted_segmentation_layout()
        time_flag_2 = time.time()
        print("Depth of DOM tree: ", self.max_level)
        print("Total segmentation time: ", time_flag_2-time_flag_1, '(s)')
        if killDriver:
            self.killDriver()

    def segment(self):
        self.segmentor = Segment(self.root_node, grainSegment=False)

    def load_precomputed(self, precomputed_dir):
        self.base_dir = precomputed_dir
        # split by "Snapshots*/"
        self.fileName = precomputed_dir.split('Snapshots/')[1].split('_')[0]
        self.imgOut = os.path.join(self.base_dir, self.fileName + '.png')
        x = json.loads(
            open(os.path.join(self.base_dir, self.fileName + '_dom.json'), 'r').read())
        self.root_node = self.toDOM(x)
        self.page_height = Image.open(self.imgOut).size[1]
        self.page_width = Image.open(self.imgOut).size[0]

    def getDomFile(self):
        return self.domOut

    def getImgFile(self):
        return self.imgOut

    def setUrl(self, urlStr):
        self.url = urlStr

        if urlStr.startswith('file:'):
            filename = urlStr.split('/')[-1]
            name = filename.split('.')[0]
            newpath = r'Snapshots/' + name + '_' + \
                str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '/'
            self.fileName = newpath + name
            os.makedirs(newpath)
            self.base_dir = newpath
            return

        if urlStr.startswith('https://') or urlStr.startswith('http://'):
            self.url = urlStr
        else:
            self.url = 'https://' + urlStr
        parse_object = urlparse(self.url)
        newpath = r'Snapshots/' + parse_object.netloc + '_' + str(
            datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '/'
        self.fileName = newpath + parse_object.netloc
        os.makedirs(newpath)
        self.base_dir = newpath

    def setDriver(self, driver=None):
        if driver is not None:
            self.browser = driver
            self.browser.implicitly_wait(1000)
            return
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--headless')
        self.browser = webdriver.Firefox(
            executable_path='/usr/local/bin/geckodriver', options=firefox_options)
        self.browser.implicitly_wait(1000)

    def getWebPage(self):
        print(self.url)
        # input()
        self.browser.get(self.url)

    def killDriver(self):
        self.browser.close()

    @staticmethod
    def toHTMLFile(page_source):
        with open("page_source.html", "w") as file:
            file.write(str(page_source))
        file.close()

    def toDOM(self, obj, parentNode=None, level=0):
        if isinstance(obj, str):
            json_obj = json.loads(obj)
        else:
            json_obj = obj
        nodeType = json_obj['nodeType']
        node = DomNode(nodeType, level)

        if level > self.max_level:
            self.max_level = level

        if nodeType == 1:  # ELEMENT NODE
            node.createElement(json_obj['tagName'], parentNode)
            attributes = json_obj['attributes']
            if attributes is not None:
                node.setAttributes(attributes)
            visual_cues = json_obj['visual_cues']
            if visual_cues is not None:
                node.setVisual_cues(visual_cues)

                this_text = visual_cues['this_text']
                if this_text is not None and this_text != "":
                    node.nodeValue = this_text
        elif nodeType == 3:
            node.createTextNode(json_obj['nodeValue'], parentNode)
            if node.parentNode is not None:
                visual_cues = node.parentNode.visual_cues
                if visual_cues is not None:
                    node.setVisual_cues(visual_cues)
        else:
            return node

        self.nodeList.append(node)
        if nodeType == 1:
            childNodes = json_obj['childNodes']
            for i in range(0, len(childNodes)):
                if childNodes[i]['nodeType'] == 1:
                    node.appendChild(self.toDOM(
                        childNodes[i], node, level + 1))
                if childNodes[i]['nodeType'] == 3:
                    try:
                        if not childNodes[i]['nodeValue'].isspace():
                            node.appendChild(self.toDOM(
                                childNodes[i], node, level + 1))
                    except KeyError:
                        print('abnormal text node')

        return node

    def getDomTree(self):
        # get dom.js full path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dom_js_path = os.path.join(dir_path, 'dom.js')
        file = open(dom_js_path, 'r')
        jscript = file.read()
        file.close()

        jscript += '\nreturn JSON.stringify(toJSON(document.getElementsByTagName("BODY")[0]));'
        x = self.browser.execute_script(jscript)

        # json_object = json.dumps(x, indent=4)
        with open(self.fileName + "_dom.json", "w") as file:
            file.write(x)
        file.close()

        self.root_node = self.toDOM(x)

    def getScreenshot(self):
        self.browser.set_window_size(self.page_width, self.page_height)
        time.sleep(1)
        self.page_height = self.browser.execute_script(
            "return document.body.parentNode.scrollHeight")
        self.browser.set_window_size(self.page_width, self.page_height)
        time.sleep(2)
        self.imgOut = self.fileName + '.png'
        self.browser.save_screenshot(self.imgOut)

    def get_segmentation_layout(self):
        self.segments = collectCascadingSegments(
            self.root_node)
        # self.segments = [segment for segment in self.nodeList if segment.isBlockNode or segment.isRecordNode]
        # for segment in self.segments:
        #     for child in segment.childNodes:
        #         if not child.isBlockNode:
        #             child.isBlockNode = True
        # self.segments = [segment for segment in self.nodeList if segment.isBlockNode or segment.isRecordNode]

        visualize_elements(image_path=self.imgOut, output_folder=self.base_dir, save_image=True,
                           customize_name="cascading_segmentation_layout.png", nodes=flatten_list(self.segments))

    def get_sheeted_segmentation_layout(self):
        segments = self.segmentor.segs
        self.sheeted_segments = []
        for key, value in segments.items():
            nodes = value.records
            value.domNode.isMerged = True
            rectangles = []
            for node in nodes:
                if not node.isMerged and isValidSegment(node):
                    rectangles.append([node.visual_cues['bounds']['x'], node.visual_cues['bounds']['y'],
                                      node.visual_cues['bounds']['width'], node.visual_cues['bounds']['height']])
                    node.isMerged = True
            if rectangles:
                self.sheeted_segments.append(merge_rectangles(rectangles))

        for seg in self.final_segments:
            bbox = [seg.visual_cues['bounds']['x'], seg.visual_cues['bounds']['y'],
                    seg.visual_cues['bounds']['width'], seg.visual_cues['bounds']['height']]
            if bbox not in self.sheeted_segments:
                self.sheeted_segments.append(bbox)

        image = cv2.imread(self.imgOut)
        i = 0
        for rect in self.sheeted_segments:
            x, y, w, h = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
            print(rect)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 3)
            # cv2.putText(image, str(i), (x, y), font = cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255,255,255), thickness=2)
        cv2.imwrite(self.base_dir+'sheeted_segmentation_layout.png', image)

    def crop_segments_and_visualize_records(self):
        segments = self.segmentor.segs
        img = cv2.imread(self.imgOut)
        for key, value in segments.items():
            if 'bbox' in value.domNode.visual_cues:
                bbox = value.domNode.visual_cues['bbox']
            else:
                bbox = value.domNode.visual_cues['bounds']
            img_cp = img.copy()
            for record in value.records:
                bbox_re = record.visual_cues['bounds']
                cv2.rectangle(img_cp, (int(bbox_re['x']), int(bbox_re['y'])), (int(
                    bbox_re['x']+bbox_re['width']), int(bbox_re['y']+bbox_re['height'])), (255, 0, 0), 3)
            try:
                crop_image = img_cp[int(bbox['y']):int(
                    bbox['y']+bbox['height']), int(bbox['x']):int(bbox['x']+bbox['width'])]
                cv2.imwrite(self.base_dir+key+'.png', crop_image)
            except:
                print('error in writing image')

    def removeOutlierSegments(self, node):
        nodes = []

        if node is None:
            return nodes

        if node.nodeName == 'body':
            for child in node.childNodes:
                if (child.isBlockNode or child.isRecordNode) and isValidSegment(child):
                    nodes.extend(self.removeOutlierSegments(child))

        valid_child_segments = []

        overlappingArea = calculate_overlap_area([node.visual_cues['bounds']['x'], node.visual_cues['bounds']['y'],
                                                 node.visual_cues['bounds']['width'], node.visual_cues['bounds']['height']], [0, 0, self.page_width, self.page_height])
        ratio = overlappingArea/(self.page_width*self.page_height)
        # width_height_condition = node.visual_cues['bounds']['width'] > 20 and node.visual_cues['bounds']['height'] > 20
        if node.isOutlier or ratio > 0.5:  # or not width_height_condition:
            for child in node.childNodes:
                if isValidSegment(child):
                    if (child.isBlockNode or child.isRecordNode):
                        valid_child_segments.append(child)
                    else:
                        nodes.extend(self.removeOutlierSegments(child))
        else:  # and width_height_condition:
            nodes.append(node)

        if valid_child_segments:
            for valid_child in valid_child_segments:
                nodes.extend(self.removeOutlierSegments(valid_child))
        return nodes

    def optimize_segmentation_layout(self):
        self.segments = [
            node for node in self.nodeList if node.isBlockNode or node.isRecordNode]
        # self.segments = flatten_list(self.segments)
        self.final_segments, size_outliers, cost_outliers, self.upper_bound = _optimize_segmentation_layout(
            list(set(self.segments)), self.max_level, self.page_width, self.page_height, self.upper_bound)

        self.final_segments = list(self.final_segments)
        visualize_elements(image_path=self.imgOut, output_folder=self.base_dir, save_image=True,
                           customize_name="segmentation_layout.png", nodes=self.final_segments)

        self.final_segments, deleted_nodes = remove_child_nodes(
            self.final_segments)
        costs = [segment.cost_variance for segment in self.final_segments]
        visualize_elements(image_path=self.imgOut, output_folder=self.base_dir, save_image=True,
                           customize_name="segmentation_layout_with_cost.png", nodes=self.final_segments, index=costs)

        costs = [segment.cost_variance for segment in cost_outliers]
        visualize_elements(image_path=self.imgOut, output_folder=self.base_dir, save_image=True,
                           customize_name="cost_outliers.png", nodes=cost_outliers, index=costs)

    def get_records_of_segment_recursively(self, node, level=10000):
        records = []
        if node is None:
            return records
        if level < 0:
            return records
        if node.isRecordNode and node.isBlockNode:
            records.append(node)
        for child in node.childNodes:
            records.extend(
                self.get_records_of_segment_recursively(child, level-1))
        return records

    def export_segmentation(self):
        segments_xpaths = [segment.attributes.get(
            "xpath", "") for segment in self.final_segments]
        segments_xpaths = {"url": self.url, "segments": segments_xpaths}
        with open("segmentations.csv", "a") as f:
            f.write(json.dumps(segments_xpaths)+"\n")

    def get_segments(self):
        segments_xpaths = [segment.attributes.get(
            "xpath", "") for segment in self.final_segments]
        siblings = []
        # print(self.segmentor.domBlocks)
        for block in self.segmentor.domBlocks:
            records = block.records
            siblings.append([record.attributes.get("xpath", "")
                            for record in records])
        return {"xpaths": segments_xpaths,
                "siblings": siblings}


def _optimize_segmentation_layout(blocks, max_level=10000, page_width=0, page_height=0, upper_bound=None):
    analysis_segments_cost_flatten(blocks, max_level)

    costs = []
    for i, block in enumerate(blocks):
        no_childs = len(_get_child_blocks(block))
        if no_childs == 0:
            no_childs = 1
        # print('no childs: ', no_childs)
        block.cost_variance = block.cost_variance/no_childs
        # size_ratio = block.visual_cues['bounds']['width'] * \
        #     block.visual_cues['bounds']['height'] / \
        #     (page_width * page_height)
        # block.cost_variance *= size_ratio

        if block.cost_variance > 0:
            costs.append(block.cost_variance)

    if len(costs) == 0:
        return [], [], blocks, upper_bound

    q1 = np.percentile(costs, 25)
    q3 = np.percentile(costs, 75)
    iqr = q3 - q1

    if not upper_bound:
        upper_bound = q3 + 1.5 * iqr

    print('upper bound: ', upper_bound)
    def isSizeOutlier(block): return block.visual_cues['bounds']['width'] < 10 or block.visual_cues['bounds']['height'] < 10 or calculate_overlap_area([block.visual_cues['bounds']['x'], block.visual_cues['bounds']['y'],
                                                                                                                                                        block.visual_cues['bounds']['width'], block.visual_cues['bounds']['height']], [0, 0, page_width, page_height])/(page_width*page_height) > 0.5
    cost_outlying_blocks = []
    for block in blocks:
        if block.cost_variance > upper_bound:
            cost_outlying_blocks.append(block)
            for child in block.childNodes:
                if child not in blocks:
                    blocks.append(child)
            # cost_outlying_blocks.extend(get_parent_nodes_recursively(block))

    cost_outlying_blocks = list(set(cost_outlying_blocks))
    size_outlying_blocks = [block for block in blocks if isSizeOutlier(block)]

    selected_blocks = [
        block for block in blocks if block not in cost_outlying_blocks and block not in size_outlying_blocks]
    return selected_blocks, size_outlying_blocks, cost_outlying_blocks, upper_bound

    # selected_blocks = [block for block in blocks if block.cost_variance <= upper_bound and not isSizeOutlier(block)]
    # size_outlying_blocks = [block for block in blocks if isSizeOutlier(block)]
    # cost_outlying_blocks = [block for block in blocks if block.cost_variance > upper_bound]
    # return selected_blocks, size_outlying_blocks, cost_outlying_blocks

# def _optimize_segmentation_layout_2(blocks, max_level=10000, page_width=0, page_height=0):

    # if len(cost) == 0:
    #     return blocks
    # q1 = np.percentile(costs, 25)
    # q3 = np.percentile(costs, 75)
    # iqr = q3 - q1

    # upper_bound = q3 + 1.5 * iqr
    # lower_bound = q1 - 1.5 * iqr

    # selected_blocks = [block for block, cost in zip(segments, costs) if cost <= upper_bound and cost >= lower_bound]
    # outlying_blocks = [block for block, cost in zip(segments, costs) if cost > upper_bound or cost < lower_bound]


def _get_child_blocks(node):
    blocks = []
    if node is None:
        return blocks
    for child in node.childNodes:
        if child.isBlockNode:
            blocks.append(child)

    return blocks


def remove_child_nodes(nodes):
    selected_nodes = []
    deleted_nodes = []
    for node in nodes:
        parent_nodes = get_parent_nodes_recursively(node)
        if any([parent_node in nodes for parent_node in parent_nodes]):
            deleted_nodes.append(node)
            continue
        selected_nodes.append(node)
    return selected_nodes, deleted_nodes


def get_parent_nodes_recursively(node):
    nodes = []
    if node is None:
        return nodes
    if node.parentNode is not None:
        nodes.append(node.parentNode)
    nodes.extend(get_parent_nodes_recursively(node.parentNode))
    return nodes
