from config import turn_off_invalid_phase_components, turn_off_required_resistances
from config import verbose_agent_preprocessing

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

def check_for_required(index_of_phase_component, unsatisfiable, pcs_to_remove, message="", is_required=False, is_resistance=False):
    not_required = not(is_required)
    # If the component isn't required, simply remove it from the available phase components.
    if not_required:
        if verbose_agent_preprocessing:
            print(f"{message} Not required, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)
    elif turn_off_invalid_phase_components:
        if verbose_agent_preprocessing:
            print(f"{message} Required but invalid, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)
    elif turn_off_required_resistances and is_resistance:
        if verbose_agent_preprocessing:
            print(f"{message} Is a resistance component, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)
    # If the component is required, append to message.
    else:
        unsatisfiable.append(message)
    return None