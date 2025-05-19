import math

def retrieve_total_time_needed(pc_list, duration_key, count_key, default_count_if_none=1):
    total_time_needed = 0
    for i in pc_list:
        total_time_needed += i[duration_key] * (i[count_key] or default_count_if_none)
    return total_time_needed

def check_if_there_is_enough_time(total_time_needed, total_availability, maximum_min_duration):
    # Check if there is enough time to complete the phase components.
    number_of_phase_components_that_need_to_fit = round(total_time_needed / maximum_min_duration)
    number_of_phase_components_that_can_fit = math.floor(total_availability / maximum_min_duration)
    if number_of_phase_components_that_need_to_fit > number_of_phase_components_that_can_fit:
        return f"Not enough time to complete the phase components. Need {total_time_needed} seconds but only have {total_availability}. Need {number_of_phase_components_that_need_to_fit} but can fit {number_of_phase_components_that_can_fit}"
    return None