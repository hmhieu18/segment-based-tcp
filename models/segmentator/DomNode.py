class DomNode:
    __slots__ = (
        'nodeType',
        'tagName', 
        'nodeName', 
        'nodeValue', 
        'visual_cues', 
        'attributes', 
        'childNodes',
        'parentNode',
        'typeOfChange',
        'mappingNode',
        'lid',
        'sn',
        'isExtracted',
        'sid',
        'mapping_id',
        'isBlockNode',
        'level',
        'isRecordNode',
        'visited',
        'isMerged',
        'cost_variance',
        'isOutlier',
        'subtree_depth',
        'xpath',
        'edit_cost')
    
    def __init__(self, nodeType, level=None):
        self.parentNode = None
        self.nodeValue = None
        self.tagName = None
        self.nodeName = None
        self.nodeType = nodeType
        self.attributes = dict()
        self.childNodes = []
        self.visual_cues = dict()
        self.typeOfChange = None
        self.lid = None
        self.sn = None
        self.isExtracted = False
        self.sid = None
        self.isBlockNode = False
        self.isRecordNode = False
        self.visited = False
        self.level = None
        self.mapping_id = None
        self.mappingNode = None
        self.isMerged = False
        self.cost_variance = 0
        self.isOutlier = False
        self.level = level
        self.subtree_depth = 0
        self.xpath = None
        self.edit_cost = 0
        
    def createElement(self, tagName, parentNode):
        self.nodeName = tagName
        self.tagName = tagName
        self.parentNode = parentNode
             
    def createTextNode(self, nodeValue, parentNode):
        self.nodeName = '#text'
        self.nodeValue = nodeValue
        self.parentNode = parentNode
        
    def createComment(self, nodeValue, parentNode):
        self.nodeName = "#comment"
        self.nodeValue = nodeValue
        self.parentNode = parentNode
    
    def setAttributes(self, attribute):
        self.attributes = attribute
    
    def setVisual_cues(self, visual_cues):
        self.visual_cues = visual_cues
    
    def appendChild(self, childNode):
        self.childNodes.append(childNode)

    def setIsBlockNode(self, isBlockNode):
        self.isBlockNode = isBlockNode
    
    def setTypeOfChange(self, type_of_change):
        self.typeOfChange = type_of_change
    
    def setMappingNode(self, mapping_node):
        self.mappingNode = mapping_node
    
    def setLevel(self, level):
        self.level = level

    def markVisited(self, visited):
        self.visited = visited
    
    def setMappingID(self, id):
        self.mapping_id = id