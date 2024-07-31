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

import json
import math
import os
import pickle
import sys

import competitors
import fast
import metric


usage = """USAGE: python py/prioritize.py <dataset> <entity> <algorithm> <repetitions>
OPTIONS:
  <dataset>: test suite to prioritize.
    options: flex_v3, grep_v3, gzip_v1, make_v1, sed_v6, closure_v0, lang_v0, math_v0, chart_v0, time_v0
  <entity>: BB or WB (function, branch, line) prioritization.
    options: bbox, function, branch, line
  <algorithm>: algorithm used for prioritization.
    options: FAST-pw, FAST-one, FAST-log, FAST-sqrt, FAST-all, STR, I-TSD, ART-D, ART-F, GT, GA, GA-S
  <repetitions>: number of prioritization to compute.
    options: positive integer value, e.g. 50
NOTE:
  STR, I-TSD are BB prioritization only.
  ART-D, ART-F, GT, GA, GA-S are WB prioritization only."""


def bboxPrioritization(name, prog, v, ctype, k, n, r, b, repeats, selsize):
    javaFlag = True if v == "v0" else False

    fin = "input/{}_{}/{}-{}.txt".format(prog, v, prog, ctype)
    if javaFlag:
        fault_matrix = "input/{}_{}/fault_matrix.pickle".format(prog, v)
    else:
        fault_matrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)
    outpath = "output/{}_{}/".format(prog, v)
    ppath = outpath + "prioritized/"

    if name == "FAST-" + selsize.__name__[:-1]:
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, bbox=True, k=k, memory=False)
                else:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, bbox=True, k=k, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "FAST-pw":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_pw(
                        fin, r, b, bbox=True, k=k, memory=False)
                else:
                    stime, ptime, prioritization = fast.fast_pw(
                        fin, r, b, bbox=True, k=k, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "STR":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.str_(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "I-TSD":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.i_tsd(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    else:
        print("Wrong input.")
        print(usage)
        exit()


def wboxPrioritization(name, prog, v, ctype, n, r, b, repeats, selsize):
    javaFlag = True if v == "v0" else False

    fin = "input/{}_{}/{}-{}.txt".format(prog, v, prog, ctype)
    if javaFlag:
        fault_matrix = "input/{}_{}/fault_matrix.pickle".format(prog, v)
    else:
        fault_matrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)

    outpath = "output/{}_{}/".format(prog, v)
    ppath = outpath + "prioritized/"

    if name == "GT":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.gt(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "FAST-" + selsize.__name__[:-1]:
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, memory=False)
                else:
                    stime, ptime, prioritization = fast.fast_(
                        fin, selsize, r=r, b=b, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "FAST-pw":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                if javaFlag:
                    stime, ptime, prioritization = fast.fast_pw(fin, r, b)
                else:
                    stime, ptime, prioritization = fast.fast_pw(
                        fin, r, b, memory=True)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    input(apfds)
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "GA":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.ga(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "GA-S":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.ga_s(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "ART-D":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.art_d(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    elif name == "ART-F":
        if ("{}-{}.tsv".format(name, ctype)) not in set(os.listdir(outpath)):
            ptimes, stimes, apfds = [], [], []
            for run in range(repeats):
                print(" Run", run)
                stime, ptime, prioritization = competitors.art_f(fin)
                writePrioritization(ppath, name, ctype, run, prioritization)
                apfd = metric.apfd(prioritization, fault_matrix, javaFlag)
                javaFlag = False
                apfds.append(apfd)
                stimes.append(stime)
                ptimes.append(ptime)
                print("  Progress: 100%  ")
                print("  Running time:", stime + ptime)
                if javaFlag:
                    print("  APFD:", sum(apfds[run]) / len(apfds[run]))
                else:
                    print("  APFD:", apfd)
            rep = (name, stimes, ptimes, apfds)
            writeOutput(outpath, ctype, rep, javaFlag)
            print("")
        else:
            print(name, "already run.")

    else:
        print("Wrong input.")
        print(usage)
        exit()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def writePrioritization(path, name, ctype, run, prioritization):
    fout = "{}/{}-{}-{}.pickle".format(path, name, ctype, run+1)
    pickle.dump(prioritization, open(fout, "wb"))


def writePrioritizationJson(path, prioritization):
    prioritization = [x-1 for x in prioritization]
    with open(path, "w") as fout:
        json.dump(prioritization, fout)


def writeOutput(outpath, ctype, res, javaFlag):
    if javaFlag:
        name, stimes, ptimes, apfds = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\n")
            for st, pt, apfdlist in zip(stimes, ptimes, apfds):
                for apfd in apfdlist:
                    tsvLine = "{}\t{}\t{}\n".format(st, pt, apfd)
                    fout.write(tsvLine)
    else:
        name, stimes, ptimes, apfds = res
        fileout = "{}/{}-{}.tsv".format(outpath, name, ctype)
        with open(fileout, "w") as fout:
            fout.write("SignatureTime\tPrioritizationTime\tAPFD\n")
            for st, pt, apfd in zip(stimes, ptimes, apfds):
                tsvLine = "{}\t{}\t{}\n".format(st, pt, apfd)
                fout.write(tsvLine)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == "__main__":
    folder = "/Users/hieu.huynh/Documents/prioritization/FAST/my_input/processed_test_suites"
    solutions = []
    repeats = 10
    for subfolder in os.listdir(folder):
        javaFlag = False
        # k, n, r, b = 5, 10, 1, 10
        #get the txt file
        txt_file = [file for file in os.listdir(os.path.join(folder, subfolder)) if file.endswith(".txt")][0]
        fin = os.path.join(folder, subfolder, txt_file)
        fault_matrix = os.path.join(folder, subfolder, "fault_matrix_key_tc.pickle")
        competitor_methods = [competitors.artf, competitors.gt, competitors.ga, competitors.ga_s]
        fast_methods = [fast.fast_pw]

        fast_solution = {}
        fast_solution["time"] = 0
        fast_solution["file"] = os.path.basename(fin).replace(".txt", ".json")
        fast_solution["sequence"] = []
        fast_solution["method"] = "fast"
        k, n, r, b = 5, 10, 1, 10
        for run in range(repeats):
            stime, ptime, prioritization = fast.fast_pw(
                            fin, r, b, memory=True)
            fast_solution["sequence"].append([x-1 for x in prioritization])
            fast_solution["time"] += stime + ptime
        fast_solution["time"] /= repeats
        solutions.append(fast_solution)

        for method in competitor_methods:
            cur_solution = {}
            cur_solution["time"] = 0
            cur_solution["file"] = os.path.basename(fin).replace(".txt", ".json")
            cur_solution["sequence"] = []
            cur_solution["method"] = method.__name__
            for run in range(repeats):
                stime, ptime, prioritization = method(fin)
                cur_solution["sequence"].append([x-1 for x in prioritization])
                cur_solution["time"] += 0
            cur_solution["time"] /= repeats
            solutions.append(cur_solution)

    with open("solutions.json", "w") as f:
        json.dump(solutions, f)

