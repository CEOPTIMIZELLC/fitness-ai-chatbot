from app import db
from app.models import Phase_Library

def check_for_out_of_bounds(item_value, min_value, max_value):
    return (min_value > item_value) or (item_value > max_value)

def add_violation(violations, phase_name, item, value_name, min_value, max_value):
    item_name = item["order"]
    item_value = item[value_name]

    if check_for_out_of_bounds(item_value, min_value, max_value):
        violation = f"Mesocycle {item_name}'s {value_name} of {item_value} exceeds {phase_name} recommended range of {min_value} <= x <= {max_value}"
        violations.append(violation)
    return violations

# Returns True if the Schedule IS within recommended parameters.
# Returns False if the Schedule IS NOT within recommended parameters.
def check_schedule_validity(schedule_list):
    violations = []

    for schedule_item in schedule_list:
        phase = db.session.get(Phase_Library, schedule_item["id"])
        phase_name = phase.name

        duration_min = phase.phase_duration_minimum_in_weeks.days // 7
        duration_max = phase.phase_duration_maximum_in_weeks.days // 7

        # Mesocycle must have a duration in weeks between the min and max allowed for the phase.
        add_violation(violations, phase_name, schedule_item, "duration", duration_min, duration_max)

    return violations
