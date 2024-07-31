from .test_interaction import Interaction
from .test_state import State
import json_fix

class TestCase:
    def __init__(self, id, interactions, status, duration, states, failure_message, order, failures) -> None:
        self.id = id
        self.order = order
        self.interactions = interactions
        self.status = status
        self.duration = duration
        self.states = states
        self.failure_message = failure_message
        self.failures = failures

    def from_json(json, segment_dict=None, filename=None, need_segment = True, order=0, failures=[]):
        interactions = []
        id = json['methodName']
        status = json['testStatus']
        if 'failureMessage' not in json:
            failure_message = ""
        else:
            failure_message = json['failureMessage']
        duration = json['duration']
        states_data = json['methodResult']['crawlStates']
        diffs = json['diffs']
        states = [State.from_json(state, diffs, segment_dict, filename, need_segment) for state in states_data]
        i = 0
        for interaction in json['methodResult']['crawlPath']:
            state = states[i]
            interactions.append(Interaction.from_json(interaction, state))
            i += 1

        return TestCase(id, interactions, status, duration, states, failure_message, order, failures)
    
    def from_generated_json(json, order=0):
        interactions = []
        id = json['id']
        status = json['status']
        failure_message = json['failure_message']
        duration = json['duration'] if 'duration' in json and json['duration'] is not None else 10
        states_data = json['states']
        failures = json.get('failures', [])
        states = [State.from_generated_json(state) for state in states_data]
        i = 0
        for interaction in json['interactions']:
            if interaction["test_object"]["id"] is None:
                continue
            state = states[i]
            interactions.append(Interaction.from_generated_json(interaction, state))
            i += 1

        return TestCase(id, interactions, status, duration, states, failure_message, order, failures)

    def get_crawl_path(self):
        crawl_path = []
        for interaction, i in zip(self.interactions, range(len(self.interactions))):
            state = self.states[i]
            crawl_item = (state, interaction)
            crawl_path.append(crawl_item)
        if len(self.states) == len(self.interactions):
            crawl_path.append((self.states[-1], None))
        return crawl_path
    
    def get_crawl_urls(self):
        urls = list(set([state.url for state in self.states]))
        return urls
    
    def get_description(self):
        description = ""
        if len(self.interactions) == 0:
            description += "Null test case"
        for interaction in self.interactions:
            description += interaction.get_description()
            description += "\n"
        # description = " ".join(self.failures)
        return description
    
    def set_text_feature(self, feature):
        self.text_feature = feature

    def get_text_feature(self):
        if hasattr(self, 'text_feature'):
            return self.text_feature
        else:
            return None


    def __str__(self) -> str:
        return f"TestCase: {self.id} {self.status} {self.duration} {self.states}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __json__(self):
        return {
            "id": self.id,
            "interactions": self.interactions,
            "status": self.status,
            "duration": self.duration,
            "states": self.states,
            "failure_message": self.failure_message,
            "order": self.order
        }
    