from config import verbose
from app.utils.get_all_exercises_for_pc import get_exercises_for_all_pcs
from .check_exercise_quantity import Main as check_exercise_quantity
from .check_for_enough_time import Main as check_for_enough_time
from .correct_parameters import correct_available_exercises_with_possible_weights, correct_minimum_duration_for_phase_component, correct_maximum_allowed_exercises_for_phase_component

def print_logging_message(message):
    if verbose:
        print(f"\n{"-" * 40}\n{message}")

# Attach allowed exercises to phase components.
def attach_exercises_to_pcs(pcs, exercises, exercises_for_pcs):
    # Attach allowed exercises to phase component.
    for pc, exercises_for_pc in zip(pcs, exercises_for_pcs):
        pc["allowed_exercises"] = exercises_for_pc
        if exercises_for_pc:
            pc["performance"]=min(exercises[exercise_for_pc-1]["performance"] for exercise_for_pc in exercises_for_pc)
        else:
            pc["performance"]=0
    return pcs

# Verifies and updates the phase component information.
# Updates the lower bound for duration if the user's current performance for all exercises in a phase component requires a higher minimum.
# Checks if the minimum amount of exercises allowed could fit into the workout with the current duration. 
# Checks if there are enough exercises to meet the minimum amount of exercises for a phase component. 
def Main(parameters, pcs, exercises, total_availability, duration_key, count_key, check_globally=False, default_count_if_none=1):
    print_logging_message("FIND EXERCISES FOR ALL PHASE COMPONENTS")
    exercises_for_pcs = get_exercises_for_all_pcs(exercises, pcs)

    print_logging_message("CORRECT POSSIBLE WEIGHTS")
    no_weighted_exercises = correct_available_exercises_with_possible_weights(pcs, exercises_for_pcs, exercises)
    if no_weighted_exercises:
        return no_weighted_exercises

    # Change the minimum allowed duration if the exercises possible don't allow for it.
    print_logging_message("CORRECT MINIMUM POSSIBLE DURATION")
    correct_minimum_duration_for_phase_component(pcs, parameters["possible_exercises"], exercises_for_pcs)

    # Check if there are enough exercises to complete the phase components.
    print_logging_message("CHECK IF THERE ARE ENOUGH EXERCISES")
    pc_without_enough_ex_message = check_exercise_quantity(pcs, exercises_for_pcs, check_globally)
    if pc_without_enough_ex_message:
        return pc_without_enough_ex_message

    print_logging_message("CORRECT MAXIMUM ALLOWED EXERCISES")
    correct_maximum_allowed_exercises_for_phase_component(pcs, exercises_for_pcs)

    # Check if there is enough time to complete the phase components.
    print_logging_message("CHECK IF THERE IS ENOUGH TIME")
    not_enough_time_message = check_for_enough_time(pcs, total_availability, duration_key, count_key, default_count_if_none)
    if not_enough_time_message:
        return not_enough_time_message

    # Attach allowed exercises to phase component.
    pcs = attach_exercises_to_pcs(pcs, exercises, exercises_for_pcs)

    return pcs, exercises