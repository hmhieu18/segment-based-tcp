from numpy import argsort
from methods.evaluation_utils import APFD
from models.test_suite import TestSuite
import json
import random
import time
from sklearn.svm import SVC
import os
import sys
import numpy as np
from methods.evaluation_utils import APFD
from sklearn.feature_extraction.text import TfidfVectorizer

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

class Terminator:
    def __init__(self, testsuite, N1=10, N2=30):
        self.fea_num = 4000
        self.N1 = N1
        self.N2 = N2
        self.E = testsuite.test_cases
        self.R = [x for x in self.E if len(x.failures) > 0]
        self.L = []
        self.LR = []
        self.extract_text_feature()

    def optimize(self):
        while len(self.L) < len(self.E):
            not_executed = [x for x in self.E if x not in self.L]
            if len(self.LR) >= 1:
                Lpre = self.presume(not_executed)
                CL = self.train(Lpre)
                X = self.query(CL, not_executed)
            else:
                # Select n random test cases
                X = random.sample(not_executed, 1)
            # Execute the selected test cases
            for x in X:
                self.execute(x)
        return self.L, [tc.order for tc in self.L]

    def presume(self, not_executed):
        # Randomly sample |L| points from not_executed, presume those to be passed test cases
        if len(not_executed) <= len(self.L):
            Lpre = self.L + not_executed
        else:
            Lpre = self.L + random.sample(not_executed, len(self.L))
        return Lpre

    def train(self, Lpre):
        # Train linear SVM with Weighting
        X_train = [tc.get_text_feature() for tc in Lpre]
        y_train = [1 if x in self.LR else 0 for x in Lpre]
        CL = SVC(kernel='linear', class_weight='balanced').fit(X_train, y_train)
        if len(self.LR) >= self.N2:
            LI = [tc.get_text_feature() for tc in Lpre if tc not in self.LR]
            LI = np.array(LI)
            choosen_tcs = argsort(CL.decision_function(LI))[:len(self.LR)]
            tmp = LI[choosen_tcs]
            X_train = np.concatenate((X_train, tmp))
            y_train = np.concatenate((y_train, np.ones(len(tmp))))
            class_weight = {0: CL.class_weight_[0], 1: CL.class_weight_[1]}
            CL = SVC(kernel='linear', class_weight=class_weight).fit(X_train, y_train)
        # input("Press Enter to continue...")
        return CL

    def query(self, CL, not_executed):
        text_features = [tc.get_text_feature() for tc in not_executed]
        if len(self.LR) >= self.N2:
            # for pair in zip(CL.decision_function(text_features), CL.predict(text_features), range(len(text_features))):
            #     print(pair)
            X = argsort(CL.decision_function(text_features))[::-1][:self.N1]
            #filter X that > 0
            # X = [x for x in X if CL.decision_function(text_features)[x] > 0]
        else:
            X = argsort(abs(CL.decision_function(text_features)))[:self.N1]
        return np.array(not_executed)[X]

    def execute(self, x):
        self.L.append(x)
        if x in self.R:
            self.LR.append(x)
        return self.LR, self.L

    def extract_text_feature(self):
        descriptions = [tc.get_description() for tc in self.E]
        tfidf_vectorizer = TfidfVectorizer(max_features=self.fea_num)
        feature_matrix = tfidf_vectorizer.fit_transform(descriptions)
        feature_array = feature_matrix.toarray()
        for tc, feature in zip(self.E, feature_array):
            tc.set_text_feature(feature)


class SVM:
    def __init__(self, kernel='linear', class_weight='balanced'):
        self.kernel = kernel
        self.class_weight = class_weight

    def svm(self, X_train, y_train):
        # Create an SVM model with a linear kernel and balanced class weights
        svm_model = SVC(kernel=self.kernel, class_weight=self.class_weight)
        svm_model.fit(X_train, y_train)
        return svm_model

    def decision_function(self, LI):
        return self.CL.decision_function(LI)


def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite


def main():
    files = os.listdir("data/test_suite_annotated")
    files = [file for file in files if file.endswith(".json")]

    cur_time = time.time()
    sum_apfd = 0
    for file in files:
        print("Processing", file)
        file = os.path.join(f"data/test_suite_annotated", file)
        folder_name = file.replace(".json", "").replace(
            "data/test_suite_annotated", f"data/test_suite_annotated/solutions-{cur_time}")
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        test_suite = parse_test_suite_from_file(file)
        test_suite.shuffle()
        export_file = os.path.join(folder_name, "terminator_solutions.json")

        terminator = Terminator(test_suite)
        ts, ordering = terminator.optimize()
        apfd = APFD(ordering, test_suite)
        print("APFD: ", apfd)
        sum_apfd += apfd

    print("Average APFD: ", sum_apfd / len(files))




if __name__ == "__main__":
    main()
