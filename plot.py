import json
import os
import random
import sys
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from methods.evaluation_utils import APFD, APSD, APOD, APOTD, APSBD, fault_coverage, segment_coverage, object_coverage, object_type_coverage, sibling_coverage
from models.test_suite import TestSuite
import copy as cp
# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

def parse_test_suite_from_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        test_suite = TestSuite.from_generated_json(json_data)
        return test_suite

def parse_solution_file(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)
        return json_data
    
def get_best_solution(json_data):
    if len(json_data) > 0:
        return json_data[0][1]

def generate_rects(n_rect, labels, n_cols=5, rect_size=10, padding=2):
    m = n_cols
    n = n_rect // m + 1
    
    rect_width = ((n_cols + 1) * padding) / n_cols
    rect_height = ((n + 1) * padding) / n

    positions = []

    for i in range(n):
        for j in range(m):
            if len(positions) == n_rect:
                break

            # Calculate the coordinates of the top-left corner of the current rectangle
            x = j * (rect_width + padding) + padding
            y = i * (rect_height + padding) + padding

            positions.append((x, y, rect_width, rect_height))

    dict_rects = {}
    max_x = 0
    max_y = 0
    # input(f"{len(positions)} {len(labels)}")
    for rect, label in zip(positions, labels):
        dict_rects[label] = rect
        x, y, w, h = rect
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)
    return dict_rects, max_x, max_y


def generate_points_in_rect(rect, num_points):
    x, y, w, h = rect
    points = []
    for _ in range(num_points):
        points.append((random.uniform(x, x + w), random.uniform(y, y + h)))
    return points

def get_list_of_points(solution, test_suite, rect_size=10, padding=2, coverage_function=segment_coverage):
    order = solution["mask"]
    ordered_test_suite = TestSuite([test_suite.test_cases[i] for i in order])
    segments_dict = coverage_function(ordered_test_suite)
    rects, max_x, max_y = generate_rects(len(segments_dict), list(segments_dict.keys()), n_cols=5, rect_size=rect_size, padding=padding)
    points = [dict() for _ in range(len(test_suite))]
    max_n_points = 0
    for i in range(len(order)):
        if i > 0:
            for key in segments_dict:
                points[i][key] = cp.deepcopy(points[i-1][key])

        for key in segments_dict:
            if key not in points[i]:
                points[i][key] = []
            if i in segments_dict[key]:
                count_i = segments_dict[key].count(i)
                points[i][key].extend(generate_points_in_rect(rects[key], count_i))
                max_n_points = max(max_n_points, len(points[i][key]))
    return rects, points, max_x, max_y, max_n_points

def get_heat_color(value, min_value, max_value):
    #color map from white to red
    cmap = plt.get_cmap("Reds")

    # Normalize the value to the range [0, 1]
    norm_value = (value - min_value) / (max_value - min_value)

    # Get the color corresponding to the normalized value
    color = cmap(norm_value)

    # Convert the matplotlib color to RGB
    r, g, b, a = color
    # input(f"{r} {g} {b}")
    return (r, g, b)

def trim_label(label, max_len=5):
    label = str(label)
    if label == None:
        return "None"
    if len(label) > max_len:
        return label[-max_len:]
    else:
        return label


def get_label(key, type):
    label = ""
    for k in key:
        label += trim_label(k) + " "
    return label

def visulize_solution(solution, test_suite, solution_name="animation", folder_out=""):
    if not os.path.exists(folder_out):
        os.makedirs(folder_out, exist_ok=True)


    # Create initial data
    rect_size = 10
    rects_seg, points_list_seg, max_x_seg, max_y_seg, max_n_points_seg = get_list_of_points(solution, test_suite, rect_size=rect_size, padding=2, coverage_function=segment_coverage)
    rects_obj, points_list_obj, max_x_obj, max_y_obj, max_n_points_obj = get_list_of_points(solution, test_suite, rect_size=rect_size, padding=2, coverage_function=object_coverage)
    rects_obj_type, points_list_obj_type, max_x_obj_type, max_y_obj_type, max_n_points_obj_type = get_list_of_points(solution, test_suite, rect_size=rect_size, padding=2, coverage_function=object_type_coverage)
    rects_sibling, points_list_sibling, max_x_sibling, max_y_sibling, max_n_points_sibling = get_list_of_points(solution, test_suite, rect_size=rect_size, padding=2, coverage_function=sibling_coverage)
    
    # Create an empty figure and axis
    fig, ((ax_seg, ax_obj), (ax_obj_type, ax_sibling)) = plt.subplots(2, 2, figsize=(10, 6))

    def update_type(ax, frame, rects, points_list, max_x, max_y, max_n_points, type):
        ax.clear()
        plot_rects = {}
        count_covered = 0
        for key in rects:
            x, y, w, h = rects[key]
            n_points = len(points_list[frame][key]) if key in points_list[frame] else 0
            if n_points > 0:
                count_covered += 1
            label = get_label(key, type)
            color = get_heat_color(n_points, 0, max_n_points)
            tmp_rect = plt.Rectangle((x, y), w, h, color=color, fill=True, edgecolor="black", linewidth=0.5)
            plot_rects[key] = {
                "rect": tmp_rect,
                "n_points": n_points,
                "label": label,
                "points": points_list[frame][key] if key in points_list[frame] else [],
            }
            ax.add_patch(plot_rects[key]["rect"])
            ax.scatter([p[0] for p in plot_rects[key]["points"]], [p[1] for p in plot_rects[key]["points"]], color="red", s=10)
            # ax.text(x + w/2, y + h/2, plot_rects[key]["label"], ha="center", va="center", color="black", fontsize=8)

        ax.set_xlim(0, max_x)
        ax.set_ylim(0, max_y)
        ax.set_title(f'{type} ({count_covered}/{len(rects)})')

    def update(frame):
        update_type(ax_seg, frame, rects_seg, points_list_seg, max_x_seg, max_y_seg, max_n_points_seg, "Segment")
        update_type(ax_obj, frame, rects_obj, points_list_obj, max_x_obj, max_y_obj, max_n_points_obj, "Object")
        update_type(ax_obj_type, frame, rects_obj_type, points_list_obj_type, max_x_obj_type, max_y_obj_type, max_n_points_obj_type, "Object Type")
        update_type(ax_sibling, frame, rects_sibling, points_list_sibling, max_x_sibling, max_y_sibling, max_n_points_sibling, "Sibling")
        #clear old text
        fig.texts = []
        fig.text(0.5, 0.04, f'Executed {frame} out of {len(test_suite)}', ha='center', fontsize=12)

    def save_frame(frame, file_out):
        update_type(ax_seg, frame, rects_seg, points_list_seg, max_x_seg, max_y_seg, max_n_points_seg, "Segment")
        update_type(ax_obj, frame, rects_obj, points_list_obj, max_x_obj, max_y_obj, max_n_points_obj, "Object")
        update_type(ax_obj_type, frame, rects_obj_type, points_list_obj_type, max_x_obj_type, max_y_obj_type, max_n_points_obj_type, "Object Type")
        update_type(ax_sibling, frame, rects_sibling, points_list_sibling, max_x_sibling, max_y_sibling, max_n_points_sibling, "Sibling")
        #clear old text
        fig.texts = []
        fig.text(0.5, 0.04, f'Executed {frame} out of {len(test_suite)}', ha='center', fontsize=12)
        plt.savefig(f"{file_out}.png")

    # Create the animation
    # animation = FuncAnimation(fig, update, frames=len(test_suite), interval=500, repeat=True)


    # # plt.tight_layout()
    # plt.show()

    # #save as gif
    # animation.save(file_out, writer='imagemagick', fps=1)
    for i in range(len(test_suite)):
        sol_folder = os.path.join(folder_out, solution_name)
        if not os.path.exists(sol_folder):
            os.makedirs(sol_folder, exist_ok=True)
        else:
            if os.path.exists(os.path.join(sol_folder, str(i) + ".png")):
                continue
        file_out = os.path.join(folder_out, solution_name, str(i))
        save_frame(i, file_out)

    plt.close(fig)


if __name__ == "__main__":
    processed_files = json.load(open("data/processed_files.json", "r"))
    for processed_file in processed_files:
        # if "pagekit" not in processed_file["test_suite_file"]:
        #     continue
        test_suite_file = processed_file["test_suite_file"]
        solution_file = processed_file["solution_file"]
        print(test_suite_file, solution_file)
        test_suite = parse_test_suite_from_file(test_suite_file)
        solution = parse_solution_file(solution_file)
        threads = []
        number_flag = False
        folder_out = os.path.dirname(solution_file)
        folder_out = os.path.join(folder_out, "visualization")
        for sol in solution:
            if not isinstance(sol[0], int):
                # if "greedy_objects" not in sol[0]:
                #     continue
                visulize_solution(sol[1], test_suite, solution_name=str(sol[0]), folder_out=folder_out)

