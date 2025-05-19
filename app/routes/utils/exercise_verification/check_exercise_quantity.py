def remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs):
    # Remove the indices that were considered impossible but weren't required.
    for i in pcs_to_remove:
        pcs.pop(i)
        exercises_for_pcs.pop(i)
    return None

# Step 1: Initial check for individual phase components
def _check_if_there_are_enough_exercises_individually(pcs, exercises_for_pcs):
    unsatisfiable = []
    pcs_to_remove = []
    for i, (pc, exercises_for_pc) in enumerate(zip(pcs, exercises_for_pcs)):
        if pc["exercises_per_bodypart_workout_min"] > len(exercises_for_pc):
            # If the component is required, append to message.
            if pc["required_within_microcycle"] == "always":
                unsatisfiable.append(
                    f"{pc["name"]} for {pc["bodypart_name"]} requires a minimum of {pc["exercises_per_bodypart_workout_min"]} to be successful but only has {len(exercises_for_pc)}"
                )
            # If the component isn't required, simply remove it from the available phase components.
            else:
                print(f"{pc["name"]} for {pc["bodypart_name"]} requires a minimum of {pc["exercises_per_bodypart_workout_min"]} to be successful but only has {len(exercises_for_pc)}. Not required, so removing from available.")
                pcs_to_remove.append(i)

    # Remove the indices that were considered impossible but weren't required.
    remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs)

    return unsatisfiable

# Step 2: Check for global feasibility
def _check_if_there_are_enough_exercises_globally(pcs, exercises_for_pcs):
    unsatisfiable = []
    pcs_to_remove = []

    # Build a list of requirements
    phase_requirements = [{
        "id": pc["phase_component_id"],
        "name": pc["name"],
        "bodypart_name": pc["bodypart_name"],
        "required_within_microcycle": pc["required_within_microcycle"],
        "required": pc["exercises_per_bodypart_workout_min"],
        "options": set(exercises_for_pc)}
        for pc, exercises_for_pc in zip(pcs, exercises_for_pcs)]

    # Try to allocate unique exercises without reuse
    used_exercises = set()

    # Sort to try harder constraints first (least options per required exercise)
    phase_requirements.sort(key=lambda x: len(x["options"]) / x["required"] if x["required"] > 0 else float("inf"))

    for i, req in enumerate(phase_requirements):
        available = req["options"] - used_exercises
        if len(available) < req["required"]:
            # If the component is required, append to message.
            if req["required_within_microcycle"] == "always":
                unsatisfiable.append(
                    f"{req["name"]} for {req["bodypart_name"]} requires {req["required"]} unique exercises, but only {len(available)} unused exercises are available."
                )
            # If the component isn't required, simply remove it from the available phase components.
            else:
                print(f"{req["name"]} for {req["bodypart_name"]} requires {req["required"]} unique exercises, but only {len(available)} unused exercises are available. Not required, so removing from available.")
                pcs_to_remove.append(i)
        else:
            # Reserve exercises
            used_exercises.update(list(available)[:req["required"]])

    # Remove the indices that were considered impossible but weren't required.
    remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs)

    return unsatisfiable

def check_if_there_are_enough_exercises(pcs, exercises_for_pcs):
    # Step 1: Initial check for individual phase components
    unsatisfiable = _check_if_there_are_enough_exercises_individually(pcs, exercises_for_pcs)
    if unsatisfiable:
        return unsatisfiable

    # Step 2: Check for global feasibility
    unsatisfiable = _check_if_there_are_enough_exercises_globally(pcs, exercises_for_pcs)
    if unsatisfiable:
        return unsatisfiable
    
    return None