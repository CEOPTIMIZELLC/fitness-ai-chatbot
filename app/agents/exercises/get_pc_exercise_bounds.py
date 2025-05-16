def get_item_bounds(min_key, max_key, items):
    return {
            "min": min(item[min_key] for item in items),
            "max": max(item[max_key] for item in items)
        }

def get_phase_component_bounds(phase_components):
    return {
        'seconds_per_exercise': get_item_bounds("seconds_per_exercise", "seconds_per_exercise", phase_components),
        'reps': get_item_bounds("reps_min", "reps_max", phase_components),
        'sets': get_item_bounds("sets_min", "sets_max", phase_components),
        'rest': get_item_bounds("rest_min", "rest_max", phase_components),
        'volume': get_item_bounds("volume_min", "volume_max", phase_components),
        'density': get_item_bounds("density_min", "density_max", phase_components),
        'duration': get_item_bounds("duration_min", "duration_max", phase_components),
        'working_duration': get_item_bounds("working_duration_min", "working_duration_max", phase_components)
    }

def get_exercise_bounds(exercises):
    return {
        'base_strain': get_item_bounds("base_strain", "base_strain", exercises),
        'intensity': {"min": 1, "max": 100},
        'one_rep_max': get_item_bounds("one_rep_max", "one_rep_max", exercises),
        "duration": get_item_bounds("duration", "duration", exercises),
        "working_duration": get_item_bounds("working_duration", "working_duration", exercises)
    }

def get_bounds(phase_components, exercises):
    scaled = 10
    pc_bounds = get_phase_component_bounds(phase_components)
    exercise_bounds = get_exercise_bounds(exercises)

    # Calculate the bounds for training weight.
    exercise_bounds["training_weight"] = {
        "min": exercise_bounds["one_rep_max"]["min"] * exercise_bounds["intensity"]["min"],
        "max": exercise_bounds["one_rep_max"]["max"] * exercise_bounds["intensity"]["max"]
        }

    # Update the bounds for volume.
    pc_bounds["volume"]["min"] *= min(exercise_bounds["training_weight"]["min"], 1)
    pc_bounds["volume"]["max"] *= exercise_bounds["training_weight"]["max"]

    # Calculate the bounds for performance.
    exercise_bounds["performance"] = {
        "min": pc_bounds["density"]["min"] * pc_bounds["volume"]["min"],
        "max": pc_bounds["density"]["max"] * pc_bounds["volume"]["max"]
        }
    
    min_intensity_strain = scaled + exercise_bounds["intensity"]["min"] + exercise_bounds["base_strain"]["min"]
    max_intensity_strain = scaled + exercise_bounds["intensity"]["max"] + exercise_bounds["base_strain"]["max"]

    min_one_exercise_effort = pc_bounds["seconds_per_exercise"]["min"] * min_intensity_strain * pc_bounds["reps"]["min"]
    max_one_exercise_effort = pc_bounds["seconds_per_exercise"]["max"] * max_intensity_strain * pc_bounds["reps"]["max"]

    # Calculate the bounds for effort.
    exercise_bounds["effort"] = {
        "min": (min_one_exercise_effort + (scaled * pc_bounds["rest"]["min"] * 5)) * pc_bounds["sets"]["min"],
        "max": (max_one_exercise_effort + (scaled * pc_bounds["rest"]["max"] * 5)) * pc_bounds["sets"]["max"]
        }

    # Calculate the bounds for working effort.
    exercise_bounds["working_effort"] = {
        "min": min_one_exercise_effort * pc_bounds["sets"]["min"],
        "max": max_one_exercise_effort * pc_bounds["sets"]["max"]
        }

    exercise_bounds["max_strain"] = int(exercise_bounds["working_effort"]["max"] / exercise_bounds["effort"]["min"] * 100)

    return pc_bounds, exercise_bounds
