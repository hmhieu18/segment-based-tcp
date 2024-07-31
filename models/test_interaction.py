from .test_object import TestObject
import json_fix

def get_parent_segment(xpath, segments):
    xpath = xpath.replace("/HTML[1]/BODY[1]", "BODY")
    for segment in segments:
        if xpath.startswith(segment):
            return segment
    return None

class Interaction:
    def __init__(self, test_object: TestObject, event_type, success) -> None:
        self.test_object = test_object
        self.event_type = event_type
        self.success = success

    def from_json(json, state):
        if 'eventable' not in json:
            return Interaction(None, None, None)
        obj_id = json['eventable']['id']
        xpath = json['eventable']['identification']['value']
        tag = json['eventable']['element']['tag']
        text = json['eventable']['element']['text']
        attributes = json['eventable']['element']['attributes']
        segment = get_parent_segment(xpath, state.segments)

        test_object = TestObject(obj_id, xpath, tag, text, attributes, segment)

        event_type = json['eventable']['eventType']
        success = json['success']
        return Interaction(test_object, event_type, success)
    
    def from_generated_json(json, state):
        obj_id = json['test_object']['id']
        xpath = json['test_object']['xpath']
        tag = json['test_object']['tag']
        text = json['test_object']['text']
        attributes = json['test_object']['attributes']
        try:
            segment = json['test_object']['segment']
        except:
            segment = get_parent_segment(xpath, state.segments)


        test_object = TestObject(obj_id, xpath, tag, text, attributes, segment)

        event_type = json['event_type']
        success = json['success']
        return Interaction(test_object, event_type, success)
    
    def get_description(self):
        description = f"User perform action {self.event_type}, on an element with tag {self.test_object.tag}, \
              text {self.test_object.text} and having xpath {self.test_object.xpath}.".strip()
        # remove multiple spaces
        description = " ".join(description.split())
        return description
    
    def __str__(self) -> str:
        return f"Interaction: {self.test_object} {self.event_type} {self.success}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __json__(self):
        return {
            "test_object": self.test_object,
            "event_type": self.event_type,
            "success": self.success
        }