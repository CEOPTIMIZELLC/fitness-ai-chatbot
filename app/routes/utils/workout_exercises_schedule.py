from app.utils.longest_string import longest_string_size_for_key

def _create_formatted_field(label: str, value: str, header_length: int) -> str:
    """Helper method to create consistently formatted fields"""
    prefix = "| " if label != "#" else ""
    formatted = f"{prefix}{value}"
    return f"{formatted:<{header_length}}"

def formatted_sub_header_line(headers):
    header_line = ""
    for label, (text, length) in headers.items():
        header_line += _create_formatted_field(text, text, length)
    return header_line

def _create_final_header_fields(longest_sizes: dict) -> dict:
    """Create all header fields with consistent formatting"""
    return {
        "superset": ("Sub", 6),
        "set": ("Set", 6),
        "number": ("No", 5),
        "exercise": ("Exercise", longest_sizes["exercise"] + 4),
        "phase_component": ("Phase Component", longest_sizes["phase_component"] + 4),
        "bodypart": ("Bodypart", longest_sizes["bodypart"] + 4),
        "warmup": ("Warmup", 9),
        "duration": ("Duration", 12),
        "working_duration": ("WDuration", 12),
        "base_strain": ("BStrain", 10),
        "seconds_per_exercise": ("Sec/Exer", 11),
        "reps": ("Reps", 7),
        "rest": ("Rest", 7),
        "one_rep_max": ("1RM", 6),
        "training_weight": ("Weight", 9),
        "intensity": ("Intensity", 12),
        "volume": ("Volume", 9),
        "density": ("Density", 10),
        "performance": ("Performance", 14),
        "end": ("", 2),
    }


def formatted_final_schedule(headers, i, exercise, set_count, superset_var):
    new_weight = exercise["weight"] or 0

    one_rep_max = round((new_weight * (30 + exercise["reps"])) / 30, 2)

    # Format line
    line_fields = {
        "set": str(set_count),
        "superset": str(superset_var["superset_current"]) if superset_var["is_resistance"] else str(superset_var["not_a_superset"]),
        "number": str(i + 1),
        "exercise": exercise["exercise_name"],
        "phase_component": f"{exercise['phase_component_subcomponent']}",
        "bodypart": exercise["bodypart_name"],
        "warmup": f"{exercise["is_warmup"]}",
        "duration": f"{exercise["duration"] // exercise["sets"]} sec",
        "working_duration": f"{exercise["working_duration"] // exercise["sets"]} sec",
        "base_strain": str(exercise["base_strain"]),
        "seconds_per_exercise": f"{exercise["seconds_per_exercise"]} sec",
        "reps": str(exercise["reps"]),
        "rest": str(exercise["rest"]),
        "one_rep_max": str(one_rep_max),
        "training_weight": str(exercise["weight"]) if exercise["weight"] else "",
        "intensity": str(exercise["intensity"]) if exercise["intensity"] else "",
        "volume": str(exercise["volume"]),
        "density": str(exercise["density"]),
        "performance": str(exercise["performance"]),
        "end": "",
    }

    line = ""
    for field, (_, length) in headers.items():
        line += _create_formatted_field(field, line_fields[field], length)
    return line + "\n"

def check_if_component_is_resistance(component_id, bodypart_id, superset_var):
    # Check if the current component is resistance.
    if component_id == 6:
        superset_var["is_resistance"] = True

        # Count up the superset count if a new superset is encountered.
        if superset_var["bodypart_id"] != bodypart_id:
            superset_var["superset_current"] += 1
        
        superset_var["bodypart_id"] = bodypart_id
    else:
        superset_var["is_resistance"] = False
    return superset_var

def log_sub_schedule(sub_schedule_name, headers, header_line, schedule, warmup=False, set_count=None):
    formatted = ""
    # Create header line
    formatted += f"\n| {sub_schedule_name} |\n"
    formatted += header_line

    superset_var = {
        "not_a_superset": "-", 
        "superset_current": 0, 
        "superset_previous": 0, 
        "bodypart_id": 0,
        "is_resistance": False}

    for component_count, exercise in enumerate(schedule):
        sub_schedule_part = exercise["is_warmup"] if warmup else not exercise["is_warmup"]
        if sub_schedule_part:
            # Count the number of occurrences of each phase component
            superset_var["superset_previous"] = superset_var["superset_current"]

            # Check if the current component is resistance.
            superset_var = check_if_component_is_resistance(exercise["component_id"], exercise["bodypart_id"], superset_var)

            if set_count:
                formatted += formatted_final_schedule(headers, component_count, exercise, set_count, superset_var)
            else:
                set_var = exercise["sets"]
                for set in range(1, set_var+1):
                    formatted += formatted_final_schedule(headers, component_count, exercise, set, superset_var)
    return formatted

def Main(loading_system_id, schedule):
    formatted = ""

    # Calculate longest string sizes
    longest_sizes = {
        "phase_component": longest_string_size_for_key(schedule, "phase_component_subcomponent"),
        "bodypart": longest_string_size_for_key(schedule, "bodypart_name"),
        "exercise": longest_string_size_for_key(schedule, "exercise_name")
    }

    # Create headers
    headers = _create_final_header_fields(longest_sizes)
    formatted += "\nFinal Training Schedule:\n" + "-" * 40 + "\n"
    header_line = formatted_sub_header_line(headers) + "\n"

    max_sets = max(exercise["sets"] if not exercise["is_warmup"] else 1 for exercise in schedule)

    # Create header line
    sub_schedule_name = "Warm-Up"

    formatted += log_sub_schedule(sub_schedule_name, headers, header_line, schedule, True)

    # Different logging method depending on if the schedule is vertical.
    if loading_system_id == 1:
        for set_count in range(1, max_sets+1):
            sub_schedule_name = f"Vertical Set {set_count}"
            formatted += log_sub_schedule(sub_schedule_name, headers, header_line, schedule, False, set_count)
    else:
        sub_schedule_name = f"Workout"
        formatted += log_sub_schedule(sub_schedule_name, headers, header_line, schedule, False)

    return formatted