import Levenshtein
from .DomNode import DomNode
from .apted import APTED, Config

# APTED configuration for removing outlier segments
def attributes_changing_cost(node1, node2):
    attributes_1 = node1.attributes
    attributes_2 = node2.attributes

    if attributes_1 == attributes_2:
        return 0

    cost = 0
    for key1, value1 in attributes_1.items():
        if any(key2 == key1 and value2 == value1 for key2, value2 in attributes_2.items()):
            continue
        else:
            cost += 1
    return cost

class CustomConfig(Config):
    def __init__(self, max_level=100, strict_text=True) -> None:
        self.max_level = max_level
        self.strict_text = strict_text
        super().__init__()

    def insert(self, node):
        return 1

    def delete(self, node):
        return 1
    
    def rename(self, node1, node2):
        """Compares attribute .value of trees"""
        cost = 0
        # difference in type of dom node
        if node1.nodeType != node2.nodeType:
            cost += 1

        # There is a difference in the tag name of nodes that have a tagName property and in the node name for the case where the tagName property does not exist.
        if node1.nodeType in [1, 3, 8, 9, 10]:
            if node1.tagName != node2.tagName:
                cost += 1
        elif node1.nodeName != node2.nodeName:
            cost += 1

        # as mentioned above, I check the nodeValue property if it exists
        if node1.nodeType in [3, 8, 2, 10, 5, 7]:
            if node1.nodeValue != node2.nodeValue:
                cost += 1

        cost += attributes_changing_cost(node1, node2)

        if self.strict_text:
            if node1.visual_cues.get('text') and node2.visual_cues.get('text'):
                tmp_cost = Levenshtein.distance(node1.visual_cues.get('text'), node2.visual_cues.get('text'))/max(len(node1.visual_cues.get('text')), len(node2.visual_cues.get('text')))
                # print(tmp_cost)
                cost += tmp_cost
            if node1.visual_cues.get('text') and not node2.visual_cues.get('text'):
                cost += 1
            if not node1.visual_cues.get('text') and node2.visual_cues.get('text'):
                cost += 1

        #font_size
        if node1.visual_cues.get('font_size') and node2.visual_cues.get('font_size'):
            if node1.visual_cues.get('font_size') != node2.visual_cues.get('font_size'):
                cost += 2
        if node1.visual_cues.get('font_size') and not node2.visual_cues.get('font_size') or not node1.visual_cues.get('font_size') and node2.visual_cues.get('font_size'):
            cost += 2

        #font_weight
        if node1.visual_cues.get('font_weight') and node2.visual_cues.get('font_weight'):
            if node1.visual_cues.get('font_weight') != node2.visual_cues.get('font_weight'):
                cost += 2
        if node1.visual_cues.get('font_weight') and not node2.visual_cues.get('font_weight') or not node1.visual_cues.get('font_weight') and node2.visual_cues.get('font_weight'):
            cost += 2
        
        #background_color
        if node1.visual_cues.get('background_color') and node2.visual_cues.get('background_color'):
            if node1.visual_cues.get('background_color') != node2.visual_cues.get('background_color'):
                cost += 5
        if node1.visual_cues.get('background_color') and not node2.visual_cues.get('background_color') or not node1.visual_cues.get('background_color') and node2.visual_cues.get('background_color'):
            cost += 5

        # self.cost_dict[(node1, node2)] = cost
        return cost

    def children(self, node):
        if len(node.childNodes) > 0:
            if node.childNodes[0].level > self.max_level:
                return []
            return node.childNodes
        else:
            return []

def count_node(node):
    if len(node.childNodes) == 0:
        return 1
    else:
        count = 1
        for child in node.childNodes:
            count += count_node(child)
        return count