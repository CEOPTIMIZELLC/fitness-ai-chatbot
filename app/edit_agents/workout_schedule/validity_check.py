from app import db
from app.models import Phase_Component_Library

def check_for_out_of_bounds(item_value, min_value, max_value):
    return (min_value > item_value) or (item_value > max_value)

def add_violation(violations, pc_name, item, value_name, min_value, max_value):
    item_name = item["exercise_name"]
    item_value = item[value_name]

    if check_for_out_of_bounds(item_value, min_value, max_value):
        violation = f"Exercise {item_name}'s {value_name} of {item_value} exceeds {pc_name} recommended range of {min_value} <= x <= {max_value}"
        violations.append(violation)
    return violations

# Returns True if the Schedule IS within recommended parameters.
# Returns False if the Schedule IS NOT within recommended parameters.
def check_schedule_validity(schedule_list):
    violations = []

    for schedule_item in schedule_list:
        pc = db.session.get(Phase_Component_Library, schedule_item["phase_component_id"])
        pc_name = pc.name

        # Exercise must have a number of reps between the min and max allowed for the phase component.
        add_violation(violations, pc_name, schedule_item, "reps", pc.reps_min, pc.reps_max)

        # Exercise must have a number of sets between the min and max allowed for the phase component.
        add_violation(violations, pc_name, schedule_item, "sets", pc.sets_min, pc.sets_max)

        # Exercise must have a rest between the min and max allowed for the phase component.
        add_violation(violations, pc_name, schedule_item, "rest", pc.rest_min, pc.rest_max)

        # Only perform for weighted excercises on phase components with a weighted range
        if schedule_item["intensity"] and pc.intensity_min and pc.intensity_max:
            # Exercise must have a intensity between the min and max allowed for the phase component.
            add_violation(violations, pc_name, schedule_item, "intensity", pc.intensity_min, pc.intensity_max)

    return violations
