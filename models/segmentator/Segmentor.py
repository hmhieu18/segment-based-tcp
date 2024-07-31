import re
from .segActions import *
from .DomBlock import DomBlock


class Segment:
    def __init__(self, root, grainSegment):
        self.root = root
        self.pruning(self.root)
        self.partial_tree_matching(grainSegment)
        self.backtracking()
        self.setIsBlockNode(self.root)
        self.cascading_segment_output()

    def pruning(self, tagbody):
        tagbody.lid = -1
        tagbody.sn = 1
        self.allnodes = [tagbody]
        i = 0
        while len(self.allnodes) > i:
            children = []
            for child in self.allnodes[i].childNodes:
                if child.nodeType == 1:
                    children.append(child)
            sn = len(children)

            for child in children:
                child.lid = i
                child.sn = sn
                self.allnodes.append(child)
            i += 1
        pass

    def partial_tree_matching(self, grainSegment=False):
        self.blocks = []

        lid_old = -2

        i = 0
        while i < len(self.allnodes):

            node = self.allnodes[i]

            if node.isExtracted:
                i += 1
                continue
            sn, lid = node.sn, node.lid

            if lid != lid_old:
                max_window_size = int(sn / 2)
                lid_old = lid

            for ws in range(1, max_window_size + 1):

                pew, cew, new = [], [], []

                for wi in range(i - ws, i + 2 * ws):

                    if wi >= 0 and wi < len(self.allnodes) and self.allnodes[wi].lid == lid and isValidSegment(self.allnodes[wi]):
                        cnode = self.allnodes[wi]
                        if wi >= i - ws and wi < i:
                            pew.append(cnode)
                        if wi >= i and wi < i + ws:
                            cew.append(cnode)
                        if wi >= i + ws and wi < i + 2 * ws:
                            new.append(cnode)

                        pass

                isle = self.__compare_nodes(pew, cew, grainSegment)
                isre = self.__compare_nodes(cew, new, grainSegment)

                if isle or isre:
                    self.blocks.append(cew)
                    self.markBlockNode(cew)
                    i += ws - 1
                    max_window_size = len(cew)
                    self.__mark_extracted(cew)
            i += 1
        pass

    def __mark_extracted(self, nodes):
        for node in nodes:
            node.isExtracted = True
            lid = node.lid
            parent = node
            while parent.parentNode is not None:
                parent = parent.parentNode
                parent.isExtracted = True
                parent.sid = lid

            nodecols = [node]
            for nodecol in nodecols:
                for child in nodecol.childNodes:
                    if child.nodeType == 1:
                        nodecols.append(child)
                nodecol.isExtracted = True

    def __compare_nodes(self, nodes1, nodes2, grainSegment=False):
        if len(nodes1) == 0 or len(nodes2) == 0:
            return False
        return self.__get_nodes_children_structure(nodes1, grainSegment) == self.__get_nodes_children_structure(nodes2, grainSegment)

    def __get_nodes_children_structure(self, nodes, grainSegment=False):
        structure = []
        for node in nodes:
            childStruct = self.__get_node_children_structure(
                node, grainSegment)
            if len(structure) > 0 and structure[-1] == childStruct and not grainSegment:
                continue
            else:
                structure.append(childStruct)
        return structure

    def __get_node_children_structure(self, node, grainSegment=False):
        nodes = [node]
        structure = []
        for node in nodes:
            for child in node.childNodes:
                if child.nodeType == 1:
                    nodes.append(child)
            # if len(structure) > 0 and structure[-1] == node.tagName and not grainSegment:
            #     continue
            # else:
            structure.append(node.tagName)
        return structure

    # def __get_node_childen_structure(self, node, grainSegment=False, structure=[]):
    #     for child in node.childNodes:
    #         if child.nodeType == 1:
    #             self.__get_node_childen_structure(child, grainSegment, structure)
    #     structure.append(node.tagName)
    #     return structure

    def backtracking(self):
        for node in self.allnodes:
            if ((node.parentNode is not None) and (not node.isExtracted) and (
                    node.parentNode.isExtracted)):
                self.blocks.append([node])
                self.markBlockNode([node])
                self.__mark_extracted([node])

    def checkSibling(self, node):
        if node.parentNode is not None:
            siblings = node.parentNode.childNodes
            for sibling in siblings:
                if sibling.isBlockNode:
                    return True
        return False

    def setIsBlockNode(self, node):
        if len(node.childNodes) == 0 or node.isBlockNode or node.nodeType == 3:
            return True
        all_block_nodes = True
        for child in node.childNodes:
            child_block_node = self.setIsBlockNode(child)
            all_block_nodes = all_block_nodes and child_block_node

        if all_block_nodes:
            node.isBlockNode = True
            self.blocks.append([node])
        return node.isBlockNode

    def setParentIsBlockNodeRecursively(self, node):
        if node.parentNode is None or node.isBlockNode:
            return
        node.parentNode.isBlockNode = True
        self.setParentIsBlockNodeRecursively(node.parentNode)

    def setIsNotBlockNode(self, node):
        if not node.childNodes:
            return node.isBlockNode

        for child in node.childNodes:
            self.setIsNotBlockNode(child)
        node.isBlockNode = False
        return node.isBlockNode

    def cascading_segment_output(self):
        segids = []
        self.segs = dict()
        self.domBlocks = []
        self.blocksNode = []

        for i, block in enumerate(self.blocks):
            domNodeList = block

            lid = block[0].lid

            if lid not in segids:
                segids.append(lid)
            sid = str(segids.index(lid))

            if block[0].parentNode and sid not in self.segs:
                block[0].parentNode.sid = sid
                self.segs[sid] = DomBlock(
                    domNodeList, block[0].parentNode, sid)

            if block[0].parentNode:
                self.segs[sid].records.extend(block)
                for node in block:
                    node.isRecordNode = True

        for key, value in self.segs.items():
            self.domBlocks.append(value)
            value.domNode.isBlockNode = True
            self.blocksNode.append(value.domNode)

    def markBlockNode(self, nodes):
        for node in nodes:
            node.isBlockNode = True
