import json_fix

class TestObject:
    def __init__(self, id, xpath, tag, text, attributes, segment) -> None:
        self.id = id
        self.xpath = xpath
        self.tag = tag
        self.text = text
        self.attributes = attributes
        self.segment = segment
    
    def __str__(self) -> str:
        return f"TestObject: id={self.id}, xpath={self.xpath}, tag={self.tag}, text={self.text}, attributes={self.attributes}, segment={self.segment}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __json__(self):
        return {
            "id": self.id,
            "xpath": self.xpath,
            "tag": self.tag,
            "text": self.text,
            "attributes": self.attributes,
            "segment": self.segment
        }