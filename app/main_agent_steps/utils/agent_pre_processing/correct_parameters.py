import heapq
from .utils import check_for_required, remove_impossible_not_required_phase_components
from config import change_min_max_exercises_for_those_available
from config import verbose_agent_preprocessing

def correct_available_exercises_with_possible_weights(pcs, exercises_for_pcs, exercises):
    unsatisfiable = []
    pcs_to_remove = []
    for i, (pc, exs_for_pc) in enumerate(zip(pcs, exercises_for_pcs)):
        # Skip if empty.
        if not exs_for_pc:
            continue

        # Retrieve range of intensities possible.
        pc_intensity = list(range(pc["intensity_min"] or 1, pc["intensity_max"] + 1))

        # Retrieve the new list of available exercises.
        available_exercises = []
        for ex_i in exs_for_pc:
            ex = exercises[ex_i-1]
            # If the exercise is weighted, determine if the user has the valid weights for it.
            if ex["is_weighted"]:
                available_weights = set(ex["weighted_equipment_measurements"])

                # Retrieve the set of possible weights by multiplying the range of intensities with the current 1RM.
                possible_weights = set([(intensity * ex["one_rep_max"] // 100) for intensity in pc_intensity])
                possible_weights_that_are_available = available_weights & possible_weights
                if possible_weights_that_are_available:
                    available_exercises.append(ex_i)

            # If the exercise isn't weighted, it doesn't need to be checked for weight.
            else:
                available_exercises.append(ex_i)
        exercises_for_pcs[i] = available_exercises
        if not exercises_for_pcs[i]:
            message = f"{pc["pc_name_for_bodypart"]} doesn't have the weights for a satisfactory intensity as well as no non-weighted exercises."
            is_required = pc["required_within_microcycle"] == "always"
            is_resistance = pc["component_name"].lower() == "resistance"
            check_for_required(i, unsatisfiable, pcs_to_remove, message, is_required, is_resistance)

    # Remove the indices that were considered impossible but weren't required.
    remove_impossible_not_required_phase_components(pcs_to_remove, pcs, exercises_for_pcs)

    return unsatisfiable

# Find the correct minimum and maximum range for the minimum duration.
def correct_minimum_duration_for_phase_component(pcs, exercises, exercises_for_pcs):
    for pc, exercises_for_pc in zip(pcs, exercises_for_pcs):
        pc_exercises_duration = [exercises[i]["duration"]# if not exercises[i]["is_weighted"] else 0
                                 for i in exercises_for_pc
                                 #if not exercises[i]["is_weighted"]
                                 ]
        if pc_exercises_duration == []:
            min_exercise_duration_min = 0
            min_exercise_duration_max = 0
        else:
            min_exercise_duration_min = heapq.nsmallest((pc["exercises_per_bodypart_workout_min"] or 1), pc_exercises_duration)[-1]# + 1
            min_exercise_duration_max = heapq.nsmallest((pc["exercises_per_bodypart_workout_max"] or 1), pc_exercises_duration)[-1]# + 1
            min_exercise_duration = heapq.nsmallest((pc["exercises_per_bodypart_workout_max"] or 1), pc_exercises_duration)

        pc["duration_min_desired"] = max(min_exercise_duration_min, pc["duration_min"])
        pc["duration_min_max"] = max(min_exercise_duration_max, pc["duration_min_max"])

    return None

def _correct_allowed_exercises(pc, key, number_of_exercises_available):
    original_value = pc.get(key)
    if original_value:
        if original_value > number_of_exercises_available:
            if verbose_agent_preprocessing:
                print(f"{pc["pc_name_for_bodypart"]}'s {key} value of {original_value} is less than the {number_of_exercises_available} exercises available. Correcting to {number_of_exercises_available}")
            pc[key] = number_of_exercises_available
    else:
        pc[key] = number_of_exercises_available
    return None

# Update the maximum exercises for a phase component if the number of exercises in the database is less than this.
def correct_min_max_allowed_exercises_for_phase_component(pcs, exercises_for_pcs):
    for pc, exercises_for_pc in zip(pcs, exercises_for_pcs):
        number_of_exercises_available = len(exercises_for_pc)
        # Correct bounds for exercises.
        if change_min_max_exercises_for_those_available:
            _correct_allowed_exercises(pc, "exercises_per_bodypart_workout_min", number_of_exercises_available)
        _correct_allowed_exercises(pc, "exercises_per_bodypart_workout_max", number_of_exercises_available)
    return None
