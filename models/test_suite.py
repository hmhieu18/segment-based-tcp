import json
from .test_case import TestCase
import random
class TestSuite:
    def __init__(self, test_cases):
        self.test_cases = test_cases
        self.segment_dict = {}

    def from_json(json, filename, need_segment = True):
        test_suite = TestSuite([])
        for test_case, i in zip(list(json.values()), range(len(json))):
            test_suite.test_cases.append(TestCase.from_json(test_case, segment_dict=test_suite.segment_dict, filename=filename, need_segment=need_segment, order=i))
            states = test_suite.test_cases[-1].states
            for state in states:
                if state.id not in test_suite.segment_dict:
                    test_suite.segment_dict[state.id] = {'segments': state.segments, 'siblings': state.siblings}

            print("Current segment dict", test_suite.segment_dict)
        return test_suite
    
    def shuffle(self):
        random.shuffle(self.test_cases)
        for i in range(len(self.test_cases)):
            self.test_cases[i].order = i
    
    def from_generated_json(json):
        test_cases = []
        for test_case, i in zip(json, range(len(json))):
            test_cases.append(TestCase.from_generated_json(test_case, order=i))
        return TestSuite(test_cases)
    
    def get_success_rate(self):
        success = 0
        for test_case in self.test_cases:
            if test_case.status == "success":
                success += 1
        return success / len(self.test_cases)
    
    def get_success_test_cases(self):
        return [test_case for test_case in self.test_cases if test_case.status == "success"]
    
    def get_failed_test_cases(self):
        return [test_case for test_case in self.test_cases if test_case.status == "failure"]
    
    def get_failure_list(self):
        failure_list = set()
        for tc in self.get_failed_test_cases():
            failure_list.add(tc.failure_message)
        return list(failure_list)

    def __str__(self) -> str:
        return f"TestSuite: {str(self.test_cases)}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __len__(self):
        return len(self.test_cases)
    
    def __getitem__(self, key):
        return self.test_cases[key]
    
    def get_crawl_paths(self):
        crawl_paths = []
        incomplete_tcs = []
        for test_case in self.test_cases:
            crawl_paths = test_case.get_crawl_path()
            crawl_paths.append(crawl_paths)
            if len(test_case.states) == len(test_case.interactions):
                incomplete_tcs.append(test_case)
        print("Incomplete test cases", len(incomplete_tcs))
        print("Total test cases", len(self.test_cases))
        return crawl_paths
    
    def get_all_states(self):
        states = []
        for test_case in self.test_cases:
            states += test_case.states
        return list(set(states))

    def get_crawl_urls(self):
        urls = []
        for test_case in self.test_cases:
            urls += test_case.get_crawl_urls()
        return list(set(urls))
    
    def export(self, file_name):
        json.dump(self.test_cases, open(file_name, "w"), indent=4)