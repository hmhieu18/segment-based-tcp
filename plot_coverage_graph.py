from collections import defaultdict
import json
import os
from ranker_revised import parse_test_suite_from_file
from methods.evaluation_utils import segment_coverage, object_coverage, object_type_coverage, sibling_coverage, fault_coverage, NAPFD
import matplotlib.pyplot as plt
import seaborn as sns
from models.test_suite import TestSuite
import random
ICONS = ["o", "v", "^", "<", ">", "s", "p", "P", "*", "h", "H", "+", "x", "X", "D", "d", "|", "_"]
COLORS = ["b", "g", "r", "c", "m", "y", "k", "w", "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan"]
CHOSEN_SOLUTIONS = [
    # "segment_based_AGEMOEA2", 
    "segment_based_AGEMOEA", 
    # "segment_based_NSGA2", 
    "ga", "random", "ga_s", "gt", "terminator", "artf"]
FORMAL_SOLUTIONS_NAME = [
    "SegTCP", 
    # "SegTCP*", 
    # "SegTCP**", 
    "GA", "Random", "GA-S", "GT", "Terminator", "ART-F"]

def get_coverage_info(solution, test_suite, coverage_function=segment_coverage, ratios=range(0, 101, 10)):
    ordered_test_suite = TestSuite([test_suite.test_cases[i] for i in solution])
    segments_dict = coverage_function(ordered_test_suite)
    coverage_dict = defaultdict(list)
    for i in range(len(ordered_test_suite.test_cases)):
        coverage_dict[i] = []
        for key, value in segments_dict.items():
            if i in value:
                coverage_dict[i].append(key)
    count_dict = defaultdict(int)
    for i in range(len(ordered_test_suite.test_cases)):
        total_objects = []
        for key, value in coverage_dict.items():
            if key <= i:
                total_objects.extend(value)
        total_objects = set(total_objects)
        count_dict[i] = len(total_objects)*100/len(segments_dict)
    ratio_dict = defaultdict(int)

    for ratio in ratios:
        n_tcs = int(len(ordered_test_suite.test_cases)*ratio/100)
        if n_tcs == 0:
            ratio_dict[ratio] = 0
            continue
        else:
            for key, value in count_dict.items():
                if key <= n_tcs:
                    ratio_dict[ratio] = value
    return ratio_dict

def draw_coverage_plot(count_dict, title):
    plt.figure(figsize=(10, 5))
    # sort the dict by key
    count_dict = dict(sorted(count_dict.items()))
    plt.plot(list(count_dict.keys()), list(count_dict.values()))
    plt.xlabel('Ratio of test cases')
    plt.ylabel('Ratio of covered objects')
    plt.title(title)
    plt.show()

def draw_coverage_multiline(chosen_solution, avg_segment_coverage_dict, filename, element="segment"):
    # draw multiple lines for each solution
    sns.set_theme(style="darkgrid")
    font_size = 30
    sns.set(font_scale=1.6)
    plt.figure(figsize=(10, 10))
    plt.rcParams.update({'font.size': font_size})
    for i, solution in enumerate(chosen_solution):
        color = COLORS[i]
        icon = ICONS[i]
        # convert solution name to formal name
        plt.plot(list(avg_segment_coverage_dict[solution].keys()), list(avg_segment_coverage_dict[solution].values()), color=color, marker=icon, label=solution, markersize=10)
    plt.xlabel('Test suite fraction', fontsize=font_size)
    plt.ylabel('Percent detected ' + element + "s", fontsize=font_size)
    # fix legend at the lower right corner
    # plt.legend(loc='lower right', borderaxespad=0., fontsize=25)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    # plt.title("Coverage of " + element + "s", fontsize=font_size)
    plt.savefig(filename)

def napfd(root_folder, json_files, ratios):
    chosen_solution = CHOSEN_SOLUTIONS
    napfd_dict = defaultdict(dict)
    folders = [folder for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, folder)) and folder != "charts"]
    for solution in chosen_solution:
        for ratio in ratios:
            napfd_dict[solution][ratio] = []
    for folder, json_file in zip(folders, json_files):
        solution_file = os.path.join(root_folder, folder, "all_solutions.json")
        solution_csv_file = os.path.join(root_folder, folder, "all_solutions.csv")

        solutions = json.load(open(solution_file, "r"))    
        test_suite = parse_test_suite_from_file(json_file)
        print(json_file)
        for sol in solutions:
            if sol[0] not in chosen_solution:
                continue
            for ratio in ratios:
                if 'mask' in sol[1]:
                    napfd = NAPFD(sol[1]['mask'], test_suite, ratio/100)
                    sol[1][f"APFD_{ratio}%"] = napfd
                        
                elif 'masks' in sol[1]:
                    sum_napfd = 0
                    for mask in sol[1]["masks"]:
                        napfd = NAPFD(mask, test_suite, ratio/100)
                        sum_napfd += napfd
                    sol[1][f"APFD_{ratio}%"] = sum_napfd/len(sol[1]["masks"])
                
                napfd_dict[sol[0]][ratio].append(sol[1][f"APFD_{ratio}%"])
        # json.dump(solutions, open(solution_file, "w"), indent=4)

    avg_napfd_dict = defaultdict(dict)
    for solution in chosen_solution:
        for ratio in ratios:
            avg_napfd_dict[solution][ratio] = sum(napfd_dict[solution][ratio])/len(napfd_dict[solution][ratio])

    json.dump(avg_napfd_dict, open("napfd.json", "w"), indent=4)

    #  draw a chart with multiple lines, each line is a method in napfd dict, x-axis is ratio, y-axis is NAPFD
    sns.set_theme(style="darkgrid")
    font_size = 30
    sns.set(font_scale=1.6)
    plt.figure(figsize=(10, 10))
    plt.rcParams.update({'font.size': font_size})
    for method in napfd_dict:
        if method not in chosen_solution:
            continue
        label = FORMAL_SOLUTIONS_NAME[CHOSEN_SOLUTIONS.index(method)]
        # [average_napfd_dict[ratio][method] for ratio in ratios]
        plt.plot(ratios, [avg_napfd_dict[method][ratio] for ratio in ratios], label=label, marker=ICONS[chosen_solution.index(method)], markersize=10, color=COLORS[chosen_solution.index(method)])
    plt.xlabel("Test suite fraction", fontsize=font_size)
    plt.ylabel("NAPFD", fontsize=font_size)
    plt.xticks(fontsize=25)
    plt.yticks(fontsize=25)
    plt.legend(loc='lower right', borderaxespad=0., fontsize=font_size)
    # plt.title("NAPFD", fontsize=font_size)
    plt.savefig(os.path.join(root_folder, "charts", "napfd.pdf"))

    
        



    

def main():
    root_folder = "data/solutions-main/solutions-all-01-12-2023 14:50:15"
    json_folder = "data/test_suite_annotated"
    if not os.path.exists(os.path.join(root_folder, "charts")):
        os.mkdir(os.path.join(root_folder, "charts"))
    folders = [folder for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, folder)) and folder != "charts"]
    json_files = [os.path.join(json_folder, folder + ".json") for folder in folders]
    ratios = range(0, 101, 10)
    segment_coverage_dict = defaultdict(dict)
    elements = ["segment", "object", "object type", "sibling", "fault"]
    coverage_functions = [segment_coverage, object_coverage, object_type_coverage, sibling_coverage, fault_coverage]
    chart_filenames = ["segment_coverage.pdf", "object_coverage.pdf", "object_type_coverage.pdf", "sibling_coverage.pdf", "fault_coverage.pdf"]
    chart_filenames = [os.path.join(root_folder, "charts", filename) for filename in chart_filenames]
    chart_titles = ["Segment coverage", "Object coverage", "Object-type coverage", "Sibling coverage", "Fault coverage"]
    json_filenames = ["Segment coverage.json", "Object coverage.json", "Object type coverage.json", "Sibling coverage.json", "Fault coverage.json"]
    json_filenames = [os.path.join(root_folder, filename) for filename in json_filenames]
    napfd(root_folder, json_files, ratios)
    # quit()
    for coverage_function, chart_filename, chart_title in list(zip(coverage_functions, chart_filenames, chart_titles)):
        # if os.path.exists(chart_filename):
        #     continue
        # if os.path.exists(json_filenames[chart_titles.index(chart_title)]):
        #     draw_coverage_multiline(FORMAL_SOLUTIONS_NAME, json.load(open(json_filenames[chart_titles.index(chart_title)], "r")), chart_filename, element=chart_title.split()[0].lower())
        #     continue
        coverage_dict = defaultdict(dict)
        for solution in FORMAL_SOLUTIONS_NAME:
            for ratio in ratios:
                coverage_dict[solution][ratio] = []
        for folder, json_file in zip(folders, json_files):
            # if "juice_shop" not in json_file and "mattermost" not in json_file:
            #     continue
            print("Processing", json_file)
            solution_file = os.path.join(root_folder, folder, "all_solutions.json")
            solution_csv_file = os.path.join(root_folder, folder, "all_solutions.csv")

            solutions = json.load(open(solution_file, "r"))    
            test_suite = parse_test_suite_from_file(json_file)

            for sol in solutions:
                if sol[0] not in CHOSEN_SOLUTIONS:
                    continue
                formal_name = FORMAL_SOLUTIONS_NAME[CHOSEN_SOLUTIONS.index(sol[0])]
                print("Processing", formal_name)
                if 'mask' in sol[1]:
                    coverage_info = get_coverage_info(sol[1]['mask'], test_suite, coverage_function=coverage_function, ratios=ratios)
                    for ratio in ratios:
                        coverage_dict[formal_name][ratio].append(coverage_info[ratio])
                else:
                    masks = sol[1]['masks']
                    if formal_name == "Random":
                            # random picks 10 masks
                            if len(sol[1]['masks']) < 10:
                                continue
                            else:
                                masks = random.sample(sol[1]['masks'], 10)
                    for mask in masks:
                        coverage_info = get_coverage_info(mask, test_suite, coverage_function=coverage_function, ratios=ratios)
                        for ratio in ratios:
                            coverage_dict[formal_name][ratio].append(coverage_info[ratio])
                        

        # calculate average
        avg_coverage_dict = defaultdict(dict)
        for solution in FORMAL_SOLUTIONS_NAME:
            for ratio in ratios:
                avg_coverage_dict[solution][ratio] = sum(coverage_dict[solution][ratio])/len(coverage_dict[solution][ratio])

        json.dump(avg_coverage_dict, open(json_filenames[chart_titles.index(chart_title)], "w"), indent=4)

        draw_coverage_multiline(FORMAL_SOLUTIONS_NAME, avg_coverage_dict, chart_filename, element=elements[coverage_functions.index(coverage_function)])



if __name__ == "__main__":
    main()