from app import db
from app.models import Phase_Library

def check_for_out_of_bounds(item_value, min_value, max_value):
    return (min_value > item_value) or (item_value > max_value)

def add_local_bounds_violation(violations, phase_name, item, value_name, min_value, max_value):
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

    # Make sure that the first phase is stabilization endurance.
    if schedule_list[0]["id"] != 1:
        violations.append(f"Mesocycle 1 is not recommended first phase of Stabilization Endurance.")

    # Make sure that the second phase is strength endurance.
    if schedule_list[1]["id"] != 2:
        violations.append(f"Mesocycle 2 is not recommended second phase of Strength Endurance.")

    phases_without_stab_end = 0
    six_phases_without_stab_end_flag = False

    for schedule_item in schedule_list:
        schedule_item_id = schedule_item["id"]

        # Reset count back to 0 if Stabilization Endurance is encountered.
        if schedule_item_id == 1:
            phases_without_stab_end = 0
        else:
            phases_without_stab_end += 1
        
        # Violation occurs if 6 or more phases go by without a stabilization endurance phase.
        if phases_without_stab_end >= 6:
            six_phases_without_stab_end_flag = True
        
        phase = db.session.get(Phase_Library, schedule_item_id)
        phase_name = phase.name

        duration_min = phase.phase_duration_minimum_in_weeks.days // 7
        duration_max = phase.phase_duration_maximum_in_weeks.days // 7

        # Mesocycle must have a duration in weeks between the min and max allowed for the phase.
        add_local_bounds_violation(violations, phase_name, schedule_item, "duration", duration_min, duration_max)

    if six_phases_without_stab_end_flag:
        violations.append(f"Six or more phases have gone by without a Stabilization Endurance Phase.")

    return violations
