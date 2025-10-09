from collections import defaultdict

def separate_by_type(input_list):
    separated_lists = defaultdict(list)
    for item in input_list:
        separated_lists[type(item)].append(item)
    return separated_lists