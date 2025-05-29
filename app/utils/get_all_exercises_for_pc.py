from config import verbose, include_all_exercises_for_desired_full_body, include_all_exercises_for_desired_bodypart, incude_all_exercises_for_desired_phase_component, include_all_exercises

def get_exercises_for_pc_conditions(exercises, phase_component, conditions=[]):
    return [i for i, exercise in enumerate(exercises, start=1) 
            if all(f(exercise, phase_component) for f in conditions)]

def get_exercises_for_pc(exercises, phase_component):
    # Retrieve range of intensities possible.
    pc_intensity = list(range(phase_component["intensity_min"] or 1, phase_component["intensity_max"] + 1))

    exercise_is_allowed_for_phase_component = lambda exercise, phase_component: phase_component["pc_ids"] in exercise["pc_ids"]
    exercise_is_of_desired_bodypart = lambda exercise, phase_component: phase_component["bodypart_id"] in exercise["bodypart_ids"]
    exercise_is_of_desired_bodypart_or_total_body = lambda exercise, phase_component: (1 in exercise["bodypart_ids"]) or (phase_component["bodypart_id"] in exercise["bodypart_ids"])

    exercise_has_valid_weights = lambda exercise, _: (
        not exercise["is_weighted"] or  # Allow all unweighted
        bool(set((intensity * exercise["one_rep_max"] // 100) for intensity in pc_intensity) & set(exercise["weighted_equipment_measurements"]))
    )

    exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                       conditions=[
                                                           exercise_is_allowed_for_phase_component,
                                                           exercise_is_of_desired_bodypart,
                                                           exercise_has_valid_weights
                                                       ])

    message = None
    pc_name = f"'{phase_component['component_name'].upper()}' '{phase_component['subcomponent_name'].upper()}'"

    # Adds all exercises for the phase component if the body part is full body.
    if include_all_exercises_for_desired_full_body and ((len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min'])) and (phase_component["bodypart_id"] == 1):
        message = f"Bodypart is total body, so all exercises for component {pc_name} will be included."
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_allowed_for_phase_component,
                                                               exercise_has_valid_weights
                                                           ])

    # Adds all exercises of a bodypart if there are still no exercises.
    if include_all_exercises_for_desired_bodypart and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        message = f"Including all exercises for bodypart '{phase_component['bodypart_name'].upper()}'."
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_of_desired_bodypart,
                                                               exercise_has_valid_weights
                                                           ])


    # Adds all exercises for a phase component if there are still no exercises.
    if incude_all_exercises_for_desired_phase_component and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        message = f"Including all exercises for component {pc_name}."
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_allowed_for_phase_component,
                                                               exercise_has_valid_weights
                                                           ])

    # Adds all exercises if there are still no exercises.
    if (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        message = f"Including all exercises."
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_has_valid_weights
                                                           ])

    if include_all_exercises and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        message = f"No solution found."

    if message and verbose:
        true_exercises_message = f"{phase_component['pc_name']} has no true exercises for bodypart '{phase_component['bodypart_name'].upper()}'."
        print(f"{true_exercises_message} {message}")
    return exercises_for_pc

# A method for retrieving the possible exercises for all phase components.
# This method removes exercises specific for a phase commponent from those that are allowed for a phase component without any true exercises.
def get_exercises_for_all_pcs(exercises, phase_components):
    number_of_possible_exercises = len(exercises)

    exercises_for_pcs = [
        get_exercises_for_pc(exercises, phase_component)
        for phase_component in phase_components
    ]

    # All phase components that have every possible exercise applied to them.
    pc_indices_without_true_exercises = [
        i
        for i in range(len(exercises_for_pcs))
        if len(exercises_for_pcs[i]) == number_of_possible_exercises
    ]

    # Remove the exercises from the phase components without true exercises for minimum searching.
    for i in pc_indices_without_true_exercises:
        # Compare to every other list of exercises that have true exercises.
        for j in range(len(exercises_for_pcs)):
            if j in pc_indices_without_true_exercises:
                continue
            exercises_for_pcs[i] = list(set(exercises_for_pcs[i]) - set(exercises_for_pcs[j]))

    return exercises_for_pcs
