import re
from models.test_suite import TestSuite


def fault_coverage(test_suite, n_tc=None):
    # Return: 
    # dict of fault:
    #   key: fault
    #   value: list of position of test case that expose the fault
    if n_tc is None:
        n_tc = len(test_suite.test_cases)
    failure_dict = dict()
    for test_case, i in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        if i >= n_tc:
            break
        if len(test_case.failures) > 0:
            failure = test_case.failures[0]
            key = failure
            if key not in failure_dict:
                failure_dict[key] = []
            failure_dict[key].append(i)
    # input(failure_dict)
    return failure_dict


def APFD(order, original_test_suite):
    # Average Percentage of fault Detection
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_fault_dict = fault_coverage(ordered_test_suite)
    sum = 0
    for key in ordered_fault_dict:
        if len(ordered_fault_dict[key]) > 0:
            pos_tc_expose_fault = ordered_fault_dict[key][0]
            sum += pos_tc_expose_fault + 1

    apfd = 1 + 1/(2*len(order)) - sum/(len(order)*len(ordered_fault_dict))
    return apfd

def NAPFD(order, original_test_suite, ratio):
    # Average Percentage of fault Detection
    no_tcs = int(len(original_test_suite.test_cases)*ratio)
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    full_ordered_fault_dict = fault_coverage(ordered_test_suite)
    ordered_fault_dict = fault_coverage(ordered_test_suite, no_tcs)
    p = len(ordered_fault_dict)/len(full_ordered_fault_dict)
    sum = 0
    for key in ordered_fault_dict:
        if len(ordered_fault_dict[key]) > 0:
            pos_tc_expose_fault = ordered_fault_dict[key][0]
            sum += pos_tc_expose_fault + 1
    if no_tcs == 0 or len(ordered_fault_dict) == 0:
        return 0
    apfd = p + p/(2*no_tcs) - sum/(no_tcs*len(full_ordered_fault_dict))
    return apfd


def APFDc(order, original_test_suite):
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_fault_dict = fault_coverage(ordered_test_suite)
    fault_dict = {key: False for key in ordered_fault_dict}
    apfdc = 0
    current_time = 0
    total_time = sum([tc.duration for tc in ordered_test_suite.test_cases])
    for tc in ordered_test_suite.test_cases:
        current_time += tc.duration
        if len(tc.failures) > 0 and not fault_dict[tc.failures[0]]:
            fault_dict[tc.failures[0]] = True
            apfdc += total_time - current_time + tc.duration/2
    apfdc = apfdc/(total_time*len(ordered_fault_dict))
    
    return apfdc




def segment_coverage(test_suite):
    segments_dict = dict()
    interations = []
    states = []
    for test_case, j in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        for interation, i in zip(test_case.interactions, range(len(test_case.interactions))):
            state = test_case.states[i]
            obj = interation.test_object
            key = str((obj.segment, state.url))
            if key not in segments_dict:
                segments_dict[key] = []
            segments_dict[key].append(j)
            interations.append(interation)
            states.append(state)

    # print("n_interactions", len(set(interations)))
    # print("n_states", len(set(states)))
    # with open("segments_dict.json", "w") as f:
    #     f.write(str(segments_dict))
    # input()
    return segments_dict


def APSD(order, original_test_suite):
    # Average Percentage of Segment Detection
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_segment_dict = segment_coverage(ordered_test_suite)
    apsd = 1 + 1/(2*len(order))
    sum = 0
    for key in ordered_segment_dict:
        if len(ordered_segment_dict[key]) > 0:
            sum += ordered_segment_dict[key][0] + 1

    apsd -= sum/(len(order)*len(ordered_segment_dict))
    return apsd


def object_type_coverage(test_suite):
    segments_dict = dict()
    for test_case, j in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        for interation, i in zip(test_case.interactions, range(len(test_case.interactions))):
            state = test_case.states[i]
            obj = interation.test_object
            key = (obj.segment, state.url, obj.tag)
            if key not in segments_dict:
                segments_dict[key] = []
            segments_dict[key].append(j)
    return segments_dict


def APOTD(order, original_test_suite):
    # Average Percentage of Object Type Detection
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_object_type_dict = object_type_coverage(ordered_test_suite)

    apotd = 1 + 1/(2*len(order))
    sum = 0
    for key in ordered_object_type_dict:
        if len(ordered_object_type_dict[key]) > 0:
            sum += ordered_object_type_dict[key][0] + 1

    apotd -= sum/(len(order)*len(ordered_object_type_dict))
    return apotd


def sibling_coverage(test_suite):
    segments_dict = dict()
    for test_case, j in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        for interation, i in zip(test_case.interactions, range(len(test_case.interactions))):
            state = test_case.states[i]
            obj = interation.test_object
            xpath = obj.xpath
            xpath_anc = xpath[:xpath.rfind("/")]
            # remove all [something]
            regex = r"\[[^\]]*\]"
            xpath_anc = re.sub(regex, "", xpath_anc)
            key = (obj.segment, state.url, xpath_anc)
            if key not in segments_dict:
                segments_dict[key] = []
            segments_dict[key].append(j)
    return segments_dict


def find_sibling_family(siblings, xpath):
    # print("Find sibling family", siblings, xpath)
    xpath = xpath.replace("/HTML[1]/BODY[1]", "BODY")
    for sibling_arr in siblings:
        if xpath in sibling_arr:
            return "_".join(sibling_arr)
    return None


def sibling_coverage_from_segmentation(test_suite):
    sibling_dict = dict()
    for test_case, j in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        for interation, i in zip(test_case.interactions, range(len(test_case.interactions))):
            state = test_case.states[i]
            obj = interation.test_object
            siblings = state.siblings
            xpath = obj.xpath
            sibling_arr = find_sibling_family(siblings, xpath)
            if sibling_arr is None:
                continue
            key = (state.url, sibling_arr)
            if key not in sibling_dict:
                sibling_dict[key] = []
            sibling_dict[key].append(j)
    return sibling_dict


def APSBD(order, original_test_suite):
    # Average Percentage of Sibling Detection
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_sibling_dict = sibling_coverage(
        ordered_test_suite)

    apsbd = 1 + 1/(2*len(order))
    sum = 0
    for key in ordered_sibling_dict:
        if len(ordered_sibling_dict[key]) > 0:
            sum += ordered_sibling_dict[key][0] + 1

    apsbd -= sum/(len(order)*len(ordered_sibling_dict))
    return apsbd


def object_coverage(test_suite):
    segments_dict = dict()
    for test_case, j in zip(test_suite.test_cases, range(len(test_suite.test_cases))):
        for interation, i in zip(test_case.interactions, range(len(test_case.interactions))):
            state = test_case.states[i]
            obj = interation.test_object
            key = (obj.xpath, state.url)
            if key not in segments_dict:
                segments_dict[key] = []
            segments_dict[key].append(j)
    return segments_dict


def APOD(order, original_test_suite):
    # Average Percentage of Object Detection
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_object_dict = object_coverage(ordered_test_suite)

    apod = 1 + 1/(2*len(order))
    sum = 0
    for key in ordered_object_dict:
        if len(ordered_object_dict[key]) > 0:
            sum += min(ordered_object_dict[key]) + 1

    apod -= sum/(len(order)*len(ordered_object_dict))
    return apod

def percentage_of_test_case_for_100_fault_coverage(order, original_test_suite):
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    ordered_fault_dict = fault_coverage(ordered_test_suite)
    last_fault_covered_test_case = 0

    for key in ordered_fault_dict:
        if len(ordered_fault_dict[key]) > 0:
            last_fault_covered_test_case = max(last_fault_covered_test_case, ordered_fault_dict[key][0])
    return last_fault_covered_test_case/len(order)

def get_object_cover_by_test_case(test_case):
    coverred_objects = set()
    for interaction, j in zip(test_case.interactions, range(len(test_case.interactions))):
        state = test_case.states[j]
        key = (state.url, interaction.test_object.xpath)
        if key not in coverred_objects:
            coverred_objects.add(key)
    return coverred_objects

def get_segment_cover_by_test_case(test_case):
    coverred_segments = set()
    for interaction, j in zip(test_case.interactions, range(len(test_case.interactions))):
        state = test_case.states[j]
        key = (state.url, interaction.test_object.segment)
        if key not in coverred_segments:
            coverred_segments.add(key)
    return coverred_segments

def get_object_type_cover_by_test_case(test_case):
    coverred_object_types = set()
    for interaction, j in zip(test_case.interactions, range(len(test_case.interactions))):
        state = test_case.states[j]
        key = (state.url, interaction.test_object.tag, interaction.test_object.segment)
        if key not in coverred_object_types:
            coverred_object_types.add(key)
    return coverred_object_types

def get_sibling_cover_by_test_case(test_case):
    coverred_siblings = []
    for interaction, j in zip(test_case.interactions, range(len(test_case.interactions))):
        state = test_case.states[j]
        xpath = interaction.test_object.xpath
        xpath_anc = xpath[:xpath.rfind("/")]
        # remove all [something]
        regex = r"\[[^\]]*\]"
        xpath_anc = re.sub(regex, "", xpath_anc)
        key = (interaction.test_object.segment, state.url, xpath_anc)

        coverred_siblings.append(key)
    return coverred_siblings

def jacard_similarity(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection)/len(union)

def object_duplication_metric(order, original_test_suite, solution=None):
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])

    objects_coverage_dict = object_coverage(ordered_test_suite)


    n = len(ordered_test_suite.test_cases)
    n_objs = len(objects_coverage_dict)

    combination_2 = n*(n-1)/2

    sum_ = 0

    for i in range(len(ordered_test_suite.test_cases)):
        objs_tci = get_object_cover_by_test_case(ordered_test_suite.test_cases[i])
        for j in range(i+1, len(ordered_test_suite.test_cases)):
            objs_tcj = get_object_cover_by_test_case(ordered_test_suite.test_cases[j])
            n_dups = len(objs_tci.intersection(objs_tcj))
            tmp = (((n-i-1)/n)**((j-i)/n))*(n_dups/n_objs)

            if solution == "gt":
                print("objects_coverage_dict", objects_coverage_dict)
                print("Obj tci", objs_tci)
                print("Obj tcj", objs_tcj)
                print('n_dups', n_dups)
                print("tmp", f"((({n}-{i}-1)/{n})**(({j}-{i})/{n}))*(n_dups/{n_objs})")
                input()

            # input()
            sum_ += tmp



    return sum_/combination_2

def object_duplication_metric_2(order, original_test_suite, element="object"):
    element_functions = [get_object_cover_by_test_case, get_segment_cover_by_test_case, get_object_type_cover_by_test_case, get_sibling_cover_by_test_case]
    elements = ["object", "segment", "object_type", "sibling"]
    element_function = element_functions[elements.index(element)]
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])

    covered_objects = []
    n = len(ordered_test_suite.test_cases)
    position_scores = [(n-i)/n for i in range(n)]

    obj_unique_scores = [0 for i in range(n)]

    for i, test_case in enumerate(ordered_test_suite.test_cases):
        objs_tci = element_function(test_case)
        if len(objs_tci) == 0:
            continue
        n_unique_objs = 0
        for obj in objs_tci:
            if obj not in covered_objects:
                n_unique_objs += 1
                covered_objects.append(obj)
        obj_unique_scores[i] = (n_unique_objs/len(objs_tci))*position_scores[i]

    result = sum(obj_unique_scores)/((n+1)/2)
    return result

def sibling_duplication_metric(order, original_test_suite):
    ordered_test_suite = TestSuite(
        [original_test_suite.test_cases[i] for i in order])
    
    siblings_coverage_dict = sibling_coverage(ordered_test_suite)
    last_sibling_covered_test_case = 0
    for key in siblings_coverage_dict:
        if len(siblings_coverage_dict[key]) > 0:
            last_sibling_covered_test_case = max(last_sibling_covered_test_case, siblings_coverage_dict[key][0])
    # print("last_sibling_covered_test_case/len(order)", f"{last_sibling_covered_test_case}/{len(order)}")
    max_duplication = sum([len(siblings_coverage_dict[key]) for key in siblings_coverage_dict])-len(siblings_coverage_dict)
    if max_duplication == 0:
        return 0
    
    duplications = 0
    sibling_covered = set()
    for i, tc in enumerate(ordered_test_suite.test_cases):
        if i > last_sibling_covered_test_case:
            break
        siblings = get_sibling_cover_by_test_case(tc)
        for sibling in siblings:
            if sibling not in sibling_covered:
                sibling_covered.add(sibling)
            else:
                duplications += 1
    # print("duplications/max_duplication", f"{duplications}/{max_duplication}")
    # input()

    return duplications/max_duplication
