class DomBlock:
    def __init__(self, domNodeList, domNode, blockID=None):
        self.domNodeList = domNodeList
        self.domNode = domNode
        self.blockID = blockID
        self.records = []