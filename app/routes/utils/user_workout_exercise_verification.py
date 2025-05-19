import heapq



def correct_available_exercises_with_possible_weights(pcs, exercises_for_pcs, exercises):
    for i, (pc, exs_for_pc) in enumerate(zip(pcs, exercises_for_pcs)):
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
    return exercises_for_pcs


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


# Update the maximum exercises for a phase component if the number of exercises in the database is less than this.
def correct_maximum_allowed_exercises_for_phase_component(pcs, exercises_for_pcs):
    for pc, exercises_for_pc in zip(pcs, exercises_for_pcs):
        number_of_exercises_available = len(exercises_for_pc)
        # Correct upper bound for exercises.
        if pc["exercises_per_bodypart_workout_max"]:
            pc["exercises_per_bodypart_workout_max"] = min(number_of_exercises_available, pc["exercises_per_bodypart_workout_max"])
        else:
            pc["exercises_per_bodypart_workout_max"] = number_of_exercises_available
    return None


def check_if_there_are_enough_exercises(pcs, exercises_for_pcs):
    # Step 1: Initial check for individual phase components
    pcs_without_enough_ex = [{"phase_component_id": pc["phase_component_id"], "name": pc["name"], 
                              "bodypart_id": pc["bodypart_id"], "bodypart_name": pc["bodypart_name"], 
                              "number_of_exercises_needed": pc["exercises_per_bodypart_workout_min"], 
                              "number_of_exercises_available": len(exercises_for_pc)}
                              for pc, exercises_for_pc in zip(pcs, exercises_for_pcs)
                              if pc["exercises_per_bodypart_workout_min"] > len(exercises_for_pc)]
    if pcs_without_enough_ex:
        return [
            f"{pc["name"]} for {pc["bodypart_name"]} requires a minimum of {pc["number_of_exercises_needed"]} to be successful but only has {pc["number_of_exercises_available"]}"
            for pc in pcs_without_enough_ex]
    
    # Step 2: Check for global feasibility
    # Build a list of requirements
    phase_requirements = [{
        "id": pc["phase_component_id"],
        "name": pc["name"],
        "bodypart_name": pc["bodypart_name"],
        "required": pc["exercises_per_bodypart_workout_min"],
        "options": set(exercises_for_pc)}
        for pc, exercises_for_pc in zip(pcs, exercises_for_pcs)]

    # Try to allocate unique exercises without reuse
    used_exercises = set()
    unsatisfiable = []

    # Sort to try harder constraints first (least options per required exercise)
    phase_requirements.sort(key=lambda x: len(x["options"]) / x["required"] if x["required"] > 0 else float("inf"))

    for req in phase_requirements:
        available = req["options"] - used_exercises
        if len(available) < req["required"]:
            unsatisfiable.append(
                f'{req["name"]} for {req["bodypart_name"]} requires {req["required"]} unique exercises, but only {len(available)} unused exercises are available'
            )
        else:
            # Reserve exercises
            used_exercises.update(list(available)[:req["required"]])
    
    if unsatisfiable:
        return unsatisfiable
    
    return None