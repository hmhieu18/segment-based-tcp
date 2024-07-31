'''
This file is part of an ICSE'18 submission that is currently under review. 
For more information visit: https://github.com/icse18-FAST/FAST.
    
This is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this source.  If not, see <http://www.gnu.org/licenses/>.
'''

from collections import defaultdict
from pickle import load


def apfd(prioritization, fault_matrix, javaFlag):
    """INPUT:
    (list)prioritization: list of prioritization of test cases
    (str)fault_matrix: path of fault_matrix (pickle file)
    (bool)javaFlag: True if output for Java fault_matrix

    OUTPUT:
    (float)APFD = 1 - (sum_{i=1}^{m} t_i / n*m) + (1 / 2n)
    n = number of test cases
    m = number of faults detected
    t_i = position of first test case revealing fault i in the prioritization
    Average Percentage of Faults Detected
    """

    # if javaFlag:
        # key=version, val=[faulty_tcs]
        # faults_dict = getFaultDetected(fault_matrix)
        # apfds = []
        # for v in range(1, len(faults_dict)+1):
        #     faulty_tcs = set(faults_dict[v])
        #     numerator = 0.0  # numerator of APFD
        #     position = 1
        #     m = 0.0
        #     for tc_ID in prioritization:
        #         if tc_ID in faulty_tcs:
        #             numerator, m = position, 1.0
        #             break
        #         position += 1

        #     n = len(prioritization)
        #     apfd = 1.0 - (numerator / (n * m)) + (1.0 / (2 * n)) if m > 0 else 0.0
        #     apfds.append(apfd)

        # return apfds

    # else:
        # dict: key=tcID, val=[detected faults]
    faults_dict = getFaultDetected(fault_matrix) if not javaFlag else getFaultDetectedJava(fault_matrix)
    input(faults_dict)
    detected_faults = set()
    numerator = 0.0  # numerator of APFD
    position = 1
    m_fault_dict = {}
    for tc_ID,i in zip(prioritization, range(len(prioritization))):
        # input(faults_dict[tc_ID])
        for fault in faults_dict[tc_ID]:
            if fault not in m_fault_dict:
                m_fault_dict[fault] = [i]
            else:
                m_fault_dict[fault].append(i)

            if fault not in detected_faults:
                detected_faults.add(fault)
                numerator += position
                print(f"Fault {fault} detected at position {position}, {i}")
        position += 1
    print(m_fault_dict)
    n, m = len(prioritization), len(detected_faults)
    apfd = 1.0 - (numerator / (n * m)) + (1.0 / (2 * n)) if m > 0 else 0.0

    return apfd


def getFaultDetected(fault_matrix):
    """INPUT:
    (str)fault_matrix: path of fault_matrix (pickle file)

    OUTPUT:
    (dict)faults_dict: key=tcID, val=[detected faults]
    """
    faults_dict = defaultdict(list)
    with open(fault_matrix, "rb") as picklefile:
        pickledict = load(picklefile)
    input(pickledict)
    for key in pickledict.keys():
        faults_dict[int(key)] = pickledict[key]
    return faults_dict

def getFaultDetectedJava(fault_matrix):
    """INPUT:
    (str)fault_matrix: path of fault_matrix (pickle file)

    OUTPUT:
    (dict)faults_dict: key=tcID, val=[detected faults]
    """
    faults_dict = defaultdict(list)

    with open(fault_matrix, "rb") as picklefile:
        pickledict = load(picklefile)
    #transpose dict, turn key into val and vice versa
    for key in pickledict.keys():
        for val in pickledict[key]:
            faults_dict[val].append(key)
    input(faults_dict)
    return faults_dict

if __name__ == "__main__":
    import os
    def get_all_pickle_files(path):
        #os walk to get all pickle files
        pickle_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".pickle"):
                    pickle_files.append(os.path.join(root, file))
        return pickle_files
    
    def get_all_bbox_files(path):
        #os walk to get all pickle files
        bbox_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith("-bbox.txt"):
                    bbox_files.append(os.path.join(root, file))
        return bbox_files
    
    def get_number_of_tcs(file):
        with open(file, "r") as f:
            lines = f.readlines()
        return len(lines)
    
    bbox_files = get_all_bbox_files("/Users/hieu.huynh/Documents/prioritization/FAST/input")
    pickle_files = get_all_pickle_files("/Users/hieu.huynh/Documents/prioritization/FAST/input")
    fails = []
    for pickle_file, bbox_file in zip(pickle_files, bbox_files):
        fault_dict = getFaultDetected(pickle_file)
        errors = set()
        for key in fault_dict.keys():
            fault_dict[key].sort()
            for val in fault_dict[key]:
                errors.add(val)
        #sort dict by key
        fault_dict = sorted(fault_dict.items(), key=lambda x: x[0])
        n_tcs = get_number_of_tcs(bbox_file)

        # print(fault_dict)
        print(os.path.dirname(pickle_file))
        print(f"Fails: {len(fault_dict)}/{n_tcs}")
        fails.append((os.path.dirname(pickle_file), len(fault_dict), n_tcs))

    with open("fails.txt", "w") as f:
        for fail in fails:
            f.write(f"{fail[0]}: {fail[1]}/{fail[2]}\n")