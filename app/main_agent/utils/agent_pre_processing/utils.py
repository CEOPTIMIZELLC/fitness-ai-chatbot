from config import turn_off_invalid_phase_components, turn_off_required_resistances
from logging_config import LogSolverPreProcessing

def turn_off_impossible_pcs(pc):
    pc["frequency_per_microcycle_min"]=0
    pc["frequency_per_microcycle_max"]=0
    pc["exercises_per_bodypart_workout_min"]=0
    pc["exercises_per_bodypart_workout_max"]=0
    if pc["required_within_microcycle"] == "always":
        pc["required_within_microcycle"]="required yet not possible"
    return pc

# Remove all of the infeasible but not required items. 
def remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs):
    # Remove the indices that were considered impossible but weren't required.
    # Sort indices in reverse so we don't shift elements prematurely
    for i in sorted(pcs_to_remove, reverse=True):
        if turn_off_required_resistances and pcs[i]["component_name"].lower() == "resistance":
            for j in range(len(pcs) - 1, -1, -1):
                if (pcs[j]["component_name"].lower() == pcs[i]["component_name"].lower() and pcs[j]["bodypart_name"].lower() == pcs[i]["bodypart_name"].lower()):
                    turn_off_impossible_pcs(pcs[j])
                    exercises_for_pcs[j] = []
        else:
            turn_off_impossible_pcs(pcs[i])
            exercises_for_pcs[i] = []
        # pcs.pop(i)
        # exercises_for_pcs.pop(i)
    return None

def log_action(message, not_required, turn_off_invalid_phase_components, is_resistance):
    if not_required:
        action = "Not required, so removing from available."
    elif turn_off_invalid_phase_components:
        action = "Required but invalid, so removing from available."
    elif turn_off_required_resistances and is_resistance:
        action = "Is a resistance component, so removing from available."
    if action:
        LogSolverPreProcessing.verbose(f"{message} {action}")
    return None

def check_for_required(index_of_phase_component, unsatisfiable, pcs_to_remove, message="", is_required=False, is_resistance=False):
    not_required = not(is_required)
    # If the component isn't required, simply remove it from the available phase components.
    if not_required or turn_off_invalid_phase_components or (turn_off_required_resistances and is_resistance):
        log_action(message, not_required, turn_off_invalid_phase_components, is_resistance)
        pcs_to_remove.append(index_of_phase_component)
    # If the component is required, append to message.
    else:
        unsatisfiable.append(message)
    return None