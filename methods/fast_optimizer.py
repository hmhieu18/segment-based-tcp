import json
import os
import pickle
import random
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from models.test_suite import TestSuite
from methods.fast.convert_to_fast_ts import conver_to_matrix, get_fault_matrix, get_all_test_object, write_matrix
    
import methods.fast.fast as fast
import methods.fast.competitors as competitors

class FASTOptimizer():
    def __init__(self, json_file: str):
        self.testsuite = json_file
        self.fin, self.fault_matrix_file = self.convert_to_fast_matrix()

    def convert_to_fast_matrix(self):
        out_matrix_file = "matrix_key_tc.txt"
        fault_matrix_file = "fault_matrix_key_tc.pickle"
        json_data = json.load(open(self.testsuite, "r"))
        matrix, tobjs = conver_to_matrix(json_data)
        write_matrix(matrix, tobjs, out_matrix_file)
        fault_matrix = get_fault_matrix(json_data)
        pickle.dump(fault_matrix, open(fault_matrix_file, "wb"))
        # input("FAST matrix and fault matrix generated")
        return out_matrix_file, fault_matrix_file
    
    def fast_optimize(self):
        k, n, r, b = 5, 10, 1, 10
        stime, ptime, prioritization = fast.fast_pw(
                        self.fin, r, b, memory=True)
        solution = [x-1 for x in prioritization]
        return solution

    def ga_optimize(self):
        stime, ptime, prioritization = competitors.ga(self.fin)
        solution = [x-1 for x in prioritization]
        return solution
    
    def gt_optimize(self):
        stime, ptime, prioritization = competitors.gt(self.fin)
        solution = [x-1 for x in prioritization]
        return solution
    
    def artf_optimize(self):
        stime, ptime, prioritization = competitors.artf(self.fin)
        solution = [x-1 for x in prioritization]
        return solution
    
    def ga_s_optimize(self):
        stime, ptime, prioritization = competitors.ga_s(self.fin)
        solution = [x-1 for x in prioritization]
        return solution
    
