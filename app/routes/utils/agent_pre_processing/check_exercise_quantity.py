from config import verbose
from .utils import check_for_required, remove_impossible_not_required_phase_components

# Step 1: Initial check for individual phase components
def _check_if_there_are_enough_exercises_individually(pcs, exercises_for_pcs):
    unsatisfiable = []
    pcs_to_remove = []
    for i, (pc, exercises_for_pc) in enumerate(zip(pcs, exercises_for_pcs)):
        if pc["exercises_per_bodypart_workout_min"] > len(exercises_for_pc):
            message = f"{pc["pc_name_for_bodypart"]} requires a minimum of {pc["exercises_per_bodypart_workout_min"]} to be successful but only has {len(exercises_for_pc)}."
            is_required = pc["required_within_microcycle"] == "always"
            is_resistance = pc["component_name"].lower() == "resistance"
            check_for_required(i, unsatisfiable, pcs_to_remove, message, is_required, is_resistance)

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
        "pc_name_for_bodypart": pc["pc_name_for_bodypart"],
        "phase_name": pc["phase_name"],
        "component_name": pc["component_name"],
        "subcomponent_name": pc["subcomponent_name"],
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
            message = f"{req["pc_name_for_bodypart"]} requires {req["required"]} unique exercises, but only {len(available)} unused exercises are available."
            is_required = req["required_within_microcycle"] == "always"
            is_resistance = req["component_name"].lower() == "resistance"
            check_for_required(i, unsatisfiable, pcs_to_remove, message, is_required, is_resistance)
        else:
            # Reserve exercises
            used_exercises.update(list(available)[:req["required"]])

    # Remove the indices that were considered impossible but weren't required.
    remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs)

    return unsatisfiable

def Main(pcs, exercises_for_pcs, check_globally=False):
    # Step 1: Initial check for individual phase components
    if verbose:
        print("LOCALLY")
    unsatisfiable = _check_if_there_are_enough_exercises_individually(pcs, exercises_for_pcs)
    if unsatisfiable:
        return unsatisfiable

    # Step 2: Check for global feasibility
    if check_globally:
        if verbose:
            print("GLOBALLY")
        unsatisfiable = _check_if_there_are_enough_exercises_globally(pcs, exercises_for_pcs)
        if unsatisfiable:
            return unsatisfiable
    
    return None