from app import db
from app.models import Phase_Component_Library

def check_for_out_of_bounds(item_value, min_value, max_value):
    return (min_value > item_value) or (item_value > max_value)

# Retrieves the phase component counters. 
# Adds an entry into the dictionary for the phase component it if one doesn't exist.
def retrieve_pc_counter_entry(pcs_encountered, pc_id, pc_name, count_min, count_max):
    if pc_id not in pcs_encountered:
        pcs_encountered[pc_id] = {
            "name": pc_name, 
            "ex_per_bodypart_min": count_min, 
            "ex_per_bodypart_max": count_max, 
            "bodypart_count": {}
        }

    return pcs_encountered[pc_id]

# Retrieves the bodypart counter. 
# Adds an entry into the dictionary for the bodypart it if one doesn't exist.
def retrieve_bodypart_count_entry(bodypart_count, bodypart_id, bodypart_name):
    if bodypart_id not in bodypart_count:
        bodypart_count[bodypart_id] = {
            "name": bodypart_name, 
            "exercises_per_bodypart": 0
        }

    return bodypart_count[bodypart_id]

def add_ex_bounds_violation(violations, pc_name, item, value_name, min_value, max_value):
    item_name = item["exercise_name"]
    item_value = item[value_name]

    if check_for_out_of_bounds(item_value, min_value, max_value):
        violation = f"Exercise {item_name}'s {value_name} of {item_value} exceeds {pc_name} recommended range of {min_value} <= x <= {max_value}"
        violations.append(violation)
    return violations

def add_pc_bounds_violation(violations, pc_name, item, value_name, min_value, max_value):
    item_name = item["name"]
    item_value = item[value_name]

    if check_for_out_of_bounds(item_value, min_value, max_value):
        violation = f"Phase Component {pc_name}'s {value_name} for Bodypart {item_name} of {item_value} exceeds recommended range of {min_value} <= x <= {max_value}"
        violations.append(violation)
    return violations

# Returns True if the Schedule IS within recommended parameters.
# Returns False if the Schedule IS NOT within recommended parameters.
def check_schedule_validity(schedule_list, user_availability):
    violations = []
    exercises_encountered = []
    general_exercises_encountered = []
    pcs_encountered = {}

    schedule_duration = 0

    for schedule_item in schedule_list:
        phase_component_id = schedule_item["phase_component_id"]

        exercises_encountered.append(schedule_item["exercise_id"])

        # Count up the total duration of the schedule for comparison later.
        schedule_duration += schedule_item["duration"]

        pc = db.session.get(Phase_Component_Library, phase_component_id)
        pc_name = pc.name

        pc_encountered = retrieve_pc_counter_entry(
            pcs_encountered, 
            phase_component_id, pc_name, 
            count_min = pc.exercises_per_bodypart_workout_min, 
            count_max = pc.exercises_per_bodypart_workout_max
        )

        bodypart_count = retrieve_bodypart_count_entry(
            pc_encountered["bodypart_count"], 
            schedule_item["bodypart_id"], 
            schedule_item["bodypart_name"]
        )
        
        bodypart_count["exercises_per_bodypart"] += 1

        # Exercise must have a number of reps, sets, and rest between the min and max allowed for the phase component.
        add_ex_bounds_violation(violations, pc_name, schedule_item, "reps", pc.reps_min, pc.reps_max)
        add_ex_bounds_violation(violations, pc_name, schedule_item, "sets", pc.sets_min, pc.sets_max)
        add_ex_bounds_violation(violations, pc_name, schedule_item, "rest", pc.rest_min, pc.rest_max)

        # Only perform for weighted excercises on phase components with a weighted range
        if schedule_item["intensity"] and pc.intensity_min and pc.intensity_max:
            add_ex_bounds_violation(violations, pc_name, schedule_item, "intensity", pc.intensity_min, pc.intensity_max)

    # Add violation for if the new schedule length exceeds the user's availability.
    if schedule_duration > user_availability:
        violations.append(f"Schedule length of {schedule_duration} exceeds user specified availability of {user_availability}.")

    # Add any violations to the number of exercises per bodypart for each phase components.
    for _, pc in pcs_encountered.items():
        pc_name = pc["name"]
        bodypart_count = pc["bodypart_count"]
        count_min = pc["ex_per_bodypart_min"] or 1
        count_max = pc["ex_per_bodypart_max"] or len(schedule_list)
        for _, bodypart in bodypart_count.items():
            add_pc_bounds_violation(violations, pc_name, bodypart, "exercises_per_bodypart", count_min, count_max)

    return violations
