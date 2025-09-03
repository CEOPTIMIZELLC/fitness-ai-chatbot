min_availability = 15 * 60
max_availability = 60 * 60

def check_for_out_of_bounds(item_value, min_value, max_value):
    return (min_value > item_value) or (item_value > max_value)

def add_violation(violations, item, value_name, min_value, max_value):
    item_name = item["weekday_name"]
    item_value = item[value_name]

    if check_for_out_of_bounds(item_value, min_value, max_value):
        violation = f"Weekday {item_name}'s {value_name} of {item_value} exceeds recommended range of {min_value} <= x <= {max_value}"
        violations.append(violation)
    return violations

# Returns True if the Schedule IS within recommended parameters.
# Returns False if the Schedule IS NOT within recommended parameters.
def check_schedule_validity(schedule_list):
    violations = []

    for schedule_item in schedule_list:
        # Availability must be between the min and max recommended for a day.
        add_violation(violations, schedule_item, "availability", min_availability, max_availability)

    return violations
