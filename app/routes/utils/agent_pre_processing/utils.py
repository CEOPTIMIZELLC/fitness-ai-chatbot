def remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs):
    # Remove the indices that were considered impossible but weren't required.
    for i in pcs_to_remove:
        pcs.pop(i)
        exercises_for_pcs.pop(i)
    return None

def check_for_required(index_of_phase_component, unsatisfiable, pcs_to_remove, conditional, message=""):
    # If the component is required, append to message.
    if conditional:
        unsatisfiable.append(message)
    # If the component isn't required, simply remove it from the available phase components.
    else:
        print(f"{message} Not required, so removing from available.")
        pcs_to_remove.append(index_of_phase_component)