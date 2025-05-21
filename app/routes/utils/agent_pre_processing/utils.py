# Remove all of the infeasible but not required items. 
def remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs):
    # Remove the indices that were considered impossible but weren't required.
    # Sort indices in reverse so we don't shift elements prematurely
    for i in sorted(pcs_to_remove, reverse=True):
        pcs.pop(i)
        exercises_for_pcs.pop(i)
    return None

def check_for_required(index_of_phase_component, unsatisfiable, pcs_to_remove, message="", is_required=False, is_resistance=False):
    not_required = not(is_required)
    # If the component isn't required, simply remove it from the available phase components.
    if not_required:
        print(f"{message} Not required, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)
    elif is_resistance:
        print(f"{message} Is a resistance component, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)
    # If the component is required, append to message.
    else:
        unsatisfiable.append(message)
    return None