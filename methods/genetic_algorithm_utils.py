from models.test_suite import TestSuite
from methods.evaluation_utils import object_coverage, segment_coverage, object_type_coverage, sibling_coverage
from methods.greedy_objects_optimizer import GreedyObjectsOptimizer
import numpy as np

def sort_genetic_solutions(order, test_suite):
    if isinstance(order, np.ndarray):
        order = order.tolist()

    ordered_test_suite = TestSuite(
        [test_suite.test_cases[i] for i in order])
    non_interacting_test_cases = []
    for i, test_case in enumerate(ordered_test_suite.test_cases):
        if len(test_case.interactions) == 0 or len(test_case.states) == 0:
            non_interacting_test_cases.append(order[i])
    non_interacting_test_cases = sorted(non_interacting_test_cases)
    print("non_interacting_test_cases: ", len(non_interacting_test_cases))
    # move the non-interacting test cases to the end of the list
    for i in non_interacting_test_cases:
        order.remove(i)
        order.append(i)
    get_last_tc_cover_all(order, test_suite)
    return order

def get_last_tc_cover_all(order, test_suite):
    if isinstance(order, np.ndarray):
        order = order.tolist()
    ordered_test_suite = TestSuite(
        [test_suite.test_cases[i] for i in order])
    objects_coverage_dict = object_coverage(ordered_test_suite)
    last_tc_cover_all_obj = 0
    for key in objects_coverage_dict:
        last_tc_cover_all_obj = max(last_tc_cover_all_obj, min(objects_coverage_dict[key]))

    segments_coverage_dict = segment_coverage(ordered_test_suite)
    last_tc_cover_all_seg = 0
    for key in segments_coverage_dict:
        last_tc_cover_all_seg = max(last_tc_cover_all_seg, min(segments_coverage_dict[key]))

    object_type_coverage_dict = object_type_coverage(ordered_test_suite)
    last_tc_cover_all_obj_type = 0
    for key in object_type_coverage_dict:
        last_tc_cover_all_obj_type = max(last_tc_cover_all_obj_type, min(object_type_coverage_dict[key]))    

    sibling_coverage_dict = sibling_coverage(ordered_test_suite)
    last_tc_cover_all_sibling = 0
    for key in sibling_coverage_dict:
        last_tc_cover_all_sibling = max(last_tc_cover_all_sibling, min(sibling_coverage_dict[key]))
    
    # last_tc_cover_all is the position of the last test
    #  case that covers all objects by the given order
    last_tc_cover_all = max(last_tc_cover_all_obj, last_tc_cover_all_seg, last_tc_cover_all_obj_type, last_tc_cover_all_sibling)
    print("Length of test suite: ", len(order))
    print("last_tc_cover_all_obj: ", last_tc_cover_all_obj)
    print("last_tc_cover_all_seg: ", last_tc_cover_all_seg)
    print("last_tc_cover_all_obj_type: ", last_tc_cover_all_obj_type)
    print("last_tc_cover_all_sibling: ", last_tc_cover_all_sibling)
    print("last_tc_cover_all: ", last_tc_cover_all)

    _, greedy_order = GreedyObjectsOptimizer(test_suite).optimize()

    need_to_sort_order = order[last_tc_cover_all+1:]
    sorted_order = []
    # sort by greedy order
    for tc in greedy_order:
        if tc in need_to_sort_order:
            sorted_order.append(tc)

    final_order = order[:last_tc_cover_all+1] + sorted_order

    return final_order
                
        
    

    
