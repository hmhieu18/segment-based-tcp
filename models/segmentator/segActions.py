from .segConfig import *
import numpy as np
import cv2
import math

# convert cascading list into 1D list
'''
Example: [1,[[2,3],[4],[5]],[6,[7],[8]],[9], 10] -> [1,2,3,4,5,6,7,8,9,10]
'''
def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def collectCascadingSegments(node):
    nodes = []
    blockNodeChildren = []

    if node is None:
        return nodes

    if node.nodeName == 'body':
        nodes.append(node)
        nodes.append(node.childNodes)
        for child in node.childNodes:
            if child.isBlockNode:
                nodes.append(collectCascadingSegments(child))
    
    if node.isBlockNode and isValidSegment(node):
        nodes.append(node)
        blockNodeChildren = []
        for child in node.childNodes:
            if child.isBlockNode:
                if isValidSegment(child):
                    blockNodeChildren.append(child)
        nodes.append(node.childNodes)

        for child in blockNodeChildren:
            nodes.append(collectCascadingSegments(child))
    return nodes


# merge bounding boxes
def merge_bbox_list(bboxes):
    if len(bboxes) == 1:
        return bboxes[0]
    else:
        return merge_bbox(bboxes[0], merge_bbox_list(bboxes[1:]))


def merge_bbox(bbox1, bbox2):
    # the bbox is a list of 4 values, the first is the x, the second is the y, the third is the width and the fourth is the height
    if 'x' not in bbox1 or 'y' not in bbox1 or 'width' not in bbox1 or 'height' not in bbox1:
        return bbox2
    if 'x' not in bbox2 or 'y' not in bbox2 or 'width' not in bbox2 or 'height' not in bbox2:
        return bbox1
    x1, y1, w1, h1 = bbox1['x'], bbox1['y'], bbox1['width'], bbox1['height']
    x2, y2, w2, h2 = bbox2['x'], bbox2['y'], bbox2['width'], bbox2['height']
    x = min(x1, x2)
    y = min(y1, y2)
    w = max(x1+w1, x2+w2) - x
    h = max(y1+h1, y2+h2) - y

    return {'x': x, 'y': y, 'width': w, 'height': h}


# return true if the node at parameter 2's bounding box is inside the node at parameter 1's bounding box
def is_inside(box_outer, box_inner):
    bounds_outer = box_outer.visual_cues['bounds']
    bounds_inner = box_inner.visual_cues['bounds']

    x_outer, y_outer, w_outer, h_outer = bounds_outer['x'], bounds_outer[
        'y'], bounds_outer['width'], bounds_outer['height']
    x_inner, y_inner, w_inner, h_inner = bounds_inner['x'], bounds_inner[
        'y'], bounds_inner['width'], bounds_inner['height']

    top_left_outer = (x_outer, y_outer)
    top_right_outer = (x_outer + w_outer, y_outer)
    bottom_left_outer = (x_outer, y_outer + h_outer)
    bottom_right_outer = (x_outer + w_outer, y_outer + h_outer)

    top_left_inner = (x_inner, y_inner)
    top_right_inner = (x_inner + w_inner, y_inner)
    bottom_left_inner = (x_inner, y_inner + h_inner)
    bottom_right_inner = (x_inner + w_inner, y_inner + h_inner)

    return (top_left_inner >= top_left_outer and
            top_right_inner <= top_right_outer and
            bottom_left_inner >= bottom_left_outer and
            bottom_right_inner <= bottom_right_outer)

# calculate the new rectangle covering all of the given rectangles
def merge_rectangles(rectangles):
    max_x = rectangles[0][0] + rectangles[0][2]
    min_x = rectangles[0][0]
    max_y = rectangles[0][1] + rectangles[0][3]
    min_y = rectangles[0][1]

    for rect in rectangles[1:]:
        max_x = max(max_x, rect[0] + rect[2])
        min_x = min(min_x, rect[0])
        max_y = max(max_y, rect[1] + rect[3])
        min_y = min(min_y, rect[1])

    width = max_x - min_x
    height = max_y - min_y

    new_rect = [min_x, min_y, width, height]

    return new_rect

#Optimize segmentation layout
def compareChildren(children, max_level):
    n = len(children)
    cost_matrix = np.zeros((n,n))

    for i in range(0, n-1):
        for j in range(i+1, n):
            ratio = 0.5
            level1 = children[i].level + children[i].subtree_depth*ratio
            level2 = children[j].level + children[j].subtree_depth*ratio
            level = min(level1, level2)
            apted = APTED(children[i], children[j], CustomConfig(level, strict_text=False))
            cost_matrix[i][j] = cost_matrix[j][i] = apted.compute_edit_distance()
    return np.std(cost_matrix)

def compareChildren_1(children, max_level):
    # child_blocks = [child for child in children if child.isBlockNode]
    child_blocks = children
    n_blocks = len(child_blocks)
    if n_blocks == 0:
        return 0
    if n_blocks == 1:
        return compareChildren_1(child_blocks[0].childNodes, max_level)
    cost_matrix = np.zeros((n_blocks, n_blocks))

    for i in range(0, n_blocks-1):
        for j in range(i+1, n_blocks):
            ratio = 0.5
            level1 = child_blocks[i].level + child_blocks[i].subtree_depth*ratio
            level2 = child_blocks[j].level + child_blocks[j].subtree_depth*ratio
            level = min(level1, level2)
            apted = APTED(child_blocks[i], child_blocks[j], CustomConfig(level, strict_text=False))
            cost_matrix[i][j] = cost_matrix[j][i] = apted.compute_edit_distance()
    return np.std(cost_matrix)



def analysis_segments_cost(segment, max_level):
    segments = []
    costs = []
    if not segment:
        return
    if len(segment[1]) == 0:
        segments.append(segment[0])
        costs.append(0)
    elif len(segment[1]) == 1:
        if len(segment)>2:
            result = analysis_segments_cost(segment[2], max_level)
            if result is not None:
                segments.extend(result[0])
                costs.extend(result[1])
        else:
            segments.append(segment[1][0])
            costs.append(0)
    else:
        segments.append(segment[0])
        segment[0].cost_variance = compareChildren(segment[1], max_level)
        costs.append(segment[0].cost_variance)
        for i in range(2, len(segment)):
            result = analysis_segments_cost(segment[i], max_level)
            if result is not None:
                segments.extend(result[0])
                costs.extend(result[1])
    return segments, costs

def analysis_segments_cost_flatten(segments, max_level):
    costs = []
    for segment in segments:
        if segment.childNodes:
            if len(segment.childNodes) == 1:
                segment.cost_variance = 0
            segment.cost_variance = compareChildren_1(segment.childNodes, max_level)
            costs.append(segment.cost_variance)
        else:
            segment.cost_variance = 0
            costs.append(0)
    return costs



def mark_outliers_iqr(segments, costs):
    q1 = np.percentile(costs, 25)
    q3 = np.percentile(costs, 75)
    iqr = q3 - q1
    
    upper_bound = q3 + 1.5 * iqr
    print("upper bound: ", upper_bound)
    
    for i in range(0, len(costs)):
        if costs[i] > upper_bound:
            segments[i].isOutlier = True


def isValidSegment(node):
    if node.nodeType == 3 and node.visual_cues['text'].strip() == "":
        return False
    return node.nodeName != 'body' and \
            node.visual_cues['visibility'] == 'visible' and \
            node.visual_cues['bounds']['width'] != 0 and \
            node.visual_cues['bounds']['height'] != 0

def collectCascadingSegments(node):
    nodes = []
    blockNodeChildren = []

    if node is None:
        return nodes

    if node.nodeName == 'body':
        nodes.append(node)
        nodes.append(node.childNodes)
        for child in node.childNodes:
            if child.isBlockNode:
                nodes.append(collectCascadingSegments(child))
    
    elif node.isBlockNode and isValidSegment(node):
        nodes.append(node)
        blockNodeChildren = []
        for child in node.childNodes:
            if child.isBlockNode:
                if isValidSegment(child):
                    blockNodeChildren.append(child)
        nodes.append(node.childNodes)

        for child in blockNodeChildren:
            nodes.append(collectCascadingSegments(child))
    return nodes


def save_subtree_depth(node):
    if not node.childNodes:
        node.subtree_depth = 0
        return

    max_child_depth = 0
    for child in node.childNodes:
        save_subtree_depth(child)
        max_child_depth = max(max_child_depth, child.subtree_depth)
    
    node.subtree_depth = 1 + max_child_depth

def fillSegments(img, segments):
    for seg in segments:
        rect = seg.visual_cues['x'], seg.visual_cues['y'], seg.visual_cues['width'], seg.visual_cues['height']
        x1, x2 = int(rect[0]), int(rect[1])
        y1, y2 = int(rect[2]), int(rect[3])
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,0,0), -1)
    return img

def overlappingArea(segment1, segment2):
    key1 = ""
    if 'bbox' in segment1.visual_cues:
            key1 = 'bbox'
    else:
        key1= 'bounds'
    key2 = ""
    if 'bbox' in segment2.visual_cues:
            key2 = 'bbox'
    else:
        key2 = 'bounds'
    
    segment1 = segment1.visual_cues[key1]
    segment2 = segment2.visual_cues[key2]

    x_overlap = max(0, min(segment1['x'] + segment1['width'], segment2['x'] + segment2['width']) - max(segment1['x'], segment2['x']))
    y_overlap = max(0, min(segment1['y'] + segment1['height'], segment2['y'] + segment2['height']) - max(segment1['y'], segment2['y']))
    return x_overlap * y_overlap

def total_overlap(segment, segments):
    return sum(overlappingArea(segment, other) for other in segments if other != segment)

def sortSegments(segments):
    sorted_segments = sorted(segments, key=lambda segment: total_overlap(segment, segments), reverse=True)
        
    

def canny_optimizing(image_path, segments):
    img = cv2.imread(image_path)
    blurred = cv2.blur(img, (3,3))
    canny = cv2.Canny(blurred, 50, 200)
    # cv2.imwrite("canny_edges.png", canny)

    for seg1 in segments:
        canny_copy = canny.copy()
        for seg2 in segments:
            if seg2 != seg1:
                #black out the segment 2 in canny
                if 'bbox' in seg2.visual_cues:
                    key = 'bbox'
                else:
                    key= 'bounds'
                offset = 2
                x = int(seg2.visual_cues[key]['x'])
                x = max(0, x-offset)

                y = int(seg2.visual_cues[key]['y'])
                y = max(0, y-offset)
                
                w = int(seg2.visual_cues[key]['width'])
                w = min(img.shape[0], w+offset)
                
                h = int(seg2.visual_cues[key]['height'])
                h = min(img.shape[1], h+offset)
                
                bbox = np.array([[x,y], [x +w, y], [x+w, y+h], [x, y+h]])
                poly = bbox.reshape((-1, 1, 2)).astype(np.int32)

                cv2.fillPoly(canny_copy, pts=[poly], color=(0, 0, 0))
        
        if 'bbox' in seg1.visual_cues:
                key = 'bbox'
        else:
            key= 'bounds'
                
        x = int(seg1.visual_cues[key]['x'])
        y = int(seg1.visual_cues[key]['y'])
        w = int(seg1.visual_cues[key]['width'])
        h = int(seg1.visual_cues[key]['height'])

        canny_copy = canny_copy[y:y+h, x:x+w]
        # cv2.imshow("canny", canny_copy)
        # cv2.waitKey(0)
        #find the non-zero min-max coords of canny
        pts = np.argwhere(canny_copy>0)
        
        if pts.shape[0] == 0 or pts.shape[1] == 0:
            continue
        
        print(pts.min(axis=0))
        y1,x1 = pts.min(axis=0)
        y2,x2 = pts.max(axis=0)

        seg1.visual_cues[key]['x'] = x1 + x
        seg1.visual_cues[key]['y'] = y1 + y
        seg1.visual_cues[key]['width'] = x2-x1
        seg1.visual_cues[key]['height'] = y2-y1

        #crop the region
        # cropped = img[y1+y:y2+y, x1+x:x2+x]
        # cv2.imwrite(f"cropped{seg1.sid}.png", cropped)
        # cv2.imwrite(f"canny_cropped{seg1.sid}.png", canny_copy)
        #cv2.waitKey(0)
                
def getCannyEdges(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

def calculate_overlap_area(box1, box2):
    x1 = box1[0]
    y1 = box1[1]
    width1 = box1[2]
    height1 = box1[3]

    x2 = box2[0]
    y2 = box2[1]
    width2 = box2[2]
    height2 = box2[3]

    # Calculate the coordinates of the intersection rectangle
    x_overlap = max(0, min(x1 + width1, x2 + width2) - max(x1, x2))
    y_overlap = max(0, min(y1 + height1, y2 + height2) - max(y1, y2))

    # Calculate the area of the intersection rectangle
    overlap_area = x_overlap * y_overlap

    return overlap_area
