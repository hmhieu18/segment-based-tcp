from collections import defaultdict
import json
import os
from ranker_revised import parse_test_suite_from_file
from methods.evaluation_utils import percentage_of_test_case_for_100_fault_coverage, APFD, APFDc, NAPFD
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid")

root_folder = "/Users/hieu.huynh/Documents/prioritization/segment-based-tcp-new/data/solutions/solutions-all-27-11-2023 19:57:20"
json_folder = "data/test_suite_annotated"
folders = [folder for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, folder))]
json_files = [os.path.join(json_folder, folder + ".json") for folder in folders]
chosen_solution = ["segment_based_AGEMOEA2", "segment_based_AGEMOEA", "segment_based_NSGA2", "ga", "random", "ga_s", "gt", "terminator", "artf"]
icons = ["o", "v", "^", "<", ">", "s", "p", "P", "*", "h", "H", "+", "x", "X", "D", "d", "|", "_"]
colors = ["b", "g", "r", "c", "m", "y", "k", "w", "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan"]
ratios = range(0, 101, 10)
napfd_dict = defaultdict(dict)
for ratio in ratios:
    for method in chosen_solution:
        napfd_dict[ratio][method] = []

for folder, json_file in zip(folders, json_files):
    # if "juice_shop_auto_mod_5.json" not in json_file:
    #     continue
    solution_file = os.path.join(root_folder, folder, "all_solutions.json")
    solution_csv_file = os.path.join(root_folder, folder, "all_solutions.csv")

    solutions = json.load(open(solution_file, "r"))    
    test_suite = parse_test_suite_from_file(json_file)
    print(json_file)
    # ratios = [100]
    # napfd_dict = defaultdict(list)
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
            
            napfd_dict[ratio][sol[0]].append(sol[1][f"APFD_{ratio}%"])
    json.dump(solutions, open(solution_file, "w"), indent=4)

    # import pandas as pd
    # # read csv file
    # df = pd.read_csv(solution_csv_file)
    # # add new column
    # for ratio in ratios:
    #     df[f"APFD_{ratio}%"] = 0
    # # convert solution column to string
    # df["solution"] = df["solution"].astype(str)
    # for sol in solutions:
    #     print(sol[0])
    #     for ratio in ratios:
    #         if len(df.loc[df['solution'] == str(sol[0])]) == 0:
    #             input()
    #         df.loc[df['solution'] == str(sol[0]), f"APFD_{ratio}%"] = sol[1][f"APFD_{ratio}%"]


    # # save to csv file
    # df.to_csv(solution_csv_file, index=False)

    # # draw a chart with multiple lines, each line is a method in napfd dict, x-axis is ratio, y-axis is NAPFD
    # sns.set_theme(style="darkgrid")
    # plt.figure(figsize=(10, 10))
    # plt.rcParams.update({'font.size': 20})
    # for method in napfd_dict:
    #     if method not in chosen_solution:
    #         continue
    #     plt.plot(ratios, napfd_dict[method], label=method, marker=icons[chosen_solution.index(method)], markersize=10, color=colors[chosen_solution.index(method)])
    # plt.xlabel("Ratio (%)")
    # plt.ylabel("NAPFD")
    # plt.legend()
    # plt.tight_layout()
    # plt.savefig(solution_csv_file.replace(".csv", ".png"))
    # plt.close()

    # # draw 0-20% ratio
    # plt.figure(figsize=(10, 10))
    # plt.rcParams.update({'font.size': 20})
    # for method in napfd_dict:
    #     if method not in chosen_solution:
    #         continue
    #     plt.plot(ratios[:10], napfd_dict[method][:10], label=method, marker=icons[chosen_solution.index(method)], markersize=10, color=colors[chosen_solution.index(method)])
    # plt.xlabel("Ratio (%)")
    # plt.ylabel("NAPFD")
    # plt.legend()
    # plt.tight_layout()
    # plt.savefig(solution_csv_file.replace(".csv", "_0_20.png"))
    # plt.close()

average_napfd_dict = defaultdict(dict)

# for each ratio, method, calculate the average NAPFD
for ratio in ratios:
    for method in napfd_dict[ratio]:
        average_napfd_dict[ratio][method] = sum(napfd_dict[ratio][method])/len(napfd_dict[ratio][method])

# draw a chart with multiple lines, each line is a method in napfd dict, x-axis is ratio, y-axis is NAPFD
sns.set_theme(style="darkgrid")
plt.figure(figsize=(10, 10))
plt.rcParams.update({'font.size': 40})
for method in napfd_dict[100]:
    if method not in chosen_solution:
        continue
    plt.plot(ratios, [average_napfd_dict[ratio][method] for ratio in ratios], label=method, marker=icons[chosen_solution.index(method)], markersize=10, color=colors[chosen_solution.index(method)])
plt.xlabel("Ratio (%)")
plt.ylabel("NAPFD")
plt.legend()
plt.tight_layout()
plt.savefig("all_solutions.png")
plt.close()
