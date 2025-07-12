import copy
from config import verbose_agent_preprocessing, verbose_exercises_for_pc_steps
from config import (
    include_all_exercises_for_desired_full_body, 
    include_all_exercises_for_desired_bodypart, 
    incude_all_exercises_for_desired_phase_component, 
    include_all_exercises)

def get_exercises_for_pc_conditions(exercises, phase_component, conditions=[]):
    return [i for i, exercise in enumerate(exercises, start=1) 
            if all(f(exercise, phase_component) for f in conditions)]

# Loop through the found exercises and determine which ones are true exercises.
def indicate_if_exercise_is_true(true_exercises, found_exercises, flag_if_not_true="No reason."):
    true_exercises_indicator = {}
    for found_exercise in found_exercises:
        # If the exercise is a true exercise, indicate this.
        if found_exercise in true_exercises:
            true_exercises_indicator[found_exercise] = "True Exercise"
        # If the exercise isn't a true exercise, indicate why it is there.
        else:
            true_exercises_indicator[found_exercise] = flag_if_not_true
    return true_exercises_indicator

def get_exercises_for_pc(exercises, phase_component):
    action_messages=[
        "INCLUDE ALL EXERCISES FOR PHASE COMPONENT SINCE TOTAL BODY:",
        "INCLUDE ALL EXERCISES FOR BODYPART:",
        "INCLUDE ALL EXERCISES FOR PHASE COMPONENT:",
        "INCLUDE ALL EXERCISES SINCE TOTAL BODY:",
        "INCLUDE ALL EXERCISES:",
        "NO SOLUTION:",
        "INCLUDE NO EXERCISES:"
        ]
    action_messages_max_length = len(max(action_messages, key=len))

    # Retrieve range of intensities possible.
    pc_intensity = list(range(phase_component["intensity_min"] or 1, phase_component["intensity_max"] + 1))

    exercise_is_allowed_for_phase_component = lambda exercise, phase_component: phase_component["pc_ids"] in exercise["pc_ids"]
    exercise_is_of_desired_bodypart = lambda exercise, phase_component: phase_component["bodypart_id"] in exercise["bodypart_ids"]
    exercise_is_of_desired_bodypart_or_total_body = lambda exercise, phase_component: (1 in exercise["bodypart_ids"]) or (phase_component["bodypart_id"] in exercise["bodypart_ids"])

    exercise_has_valid_weights = lambda exercise, _: (
        not exercise["is_weighted"] or  # Allow all unweighted
        bool(set((intensity * exercise["one_rep_max"] // 100) for intensity in pc_intensity) & set(exercise["weighted_equipment_measurements"]))
    )

    # True Exercises for the PC at the bodypart.
    exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                       conditions=[
                                                           exercise_is_allowed_for_phase_component,
                                                           exercise_is_of_desired_bodypart,
                                                           exercise_has_valid_weights
                                                       ])
    
    true_exercises_for_pc = copy.deepcopy(exercises_for_pc)

    message = None
    pc_name = f"'{phase_component['component_name'].upper()}' '{phase_component['subcomponent_name'].upper()}'"
    true_exercises_message = f"{phase_component['pc_name']} doesn't have enough exercises for bodypart '{phase_component['bodypart_name'].upper()}'."

    # Adds all exercises for the phase component if the body part is full body.
    if include_all_exercises_for_desired_full_body and ((len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min'])) and (phase_component["bodypart_id"] == 1):
        action_message = action_messages[0]
        message = f"Bodypart is total body, so all exercises for component {pc_name} will be included."
        if verbose_exercises_for_pc_steps:
            print(f"{action_message} {true_exercises_message} {message}")
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_allowed_for_phase_component,
                                                               exercise_has_valid_weights
                                                           ])

    # Adds all exercises of a bodypart if there are still no exercises.
    if include_all_exercises_for_desired_bodypart and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        action_message = action_messages[1]
        message = f"Including all exercises for bodypart '{phase_component['bodypart_name'].upper()}'."
        if verbose_exercises_for_pc_steps:
            print(f"{action_message} {true_exercises_message} {message}")
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_of_desired_bodypart,
                                                               exercise_has_valid_weights
                                                           ])


    # Adds all exercises for a phase component if there are still no exercises.
    if incude_all_exercises_for_desired_phase_component and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        action_message = action_messages[2]
        message = f"Including all exercises for component {pc_name}."
        if verbose_exercises_for_pc_steps:
            print(f"{action_message} {true_exercises_message} {message}")
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_is_allowed_for_phase_component,
                                                               exercise_has_valid_weights
                                                           ])

    # Adds all exercises if the body part is full body.
    if include_all_exercises_for_desired_full_body and include_all_exercises_for_desired_bodypart and ((len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min'])) and (phase_component["bodypart_id"] == 1):
        action_message = action_messages[3]
        message = f"Bodypart is total body, so all exercises for component {pc_name} will be included."
        if verbose_exercises_for_pc_steps:
            print(f"{action_message} {true_exercises_message} {message}")
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_has_valid_weights
                                                           ])

    # Adds all exercises if there are still no exercises.
    if include_all_exercises and (len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']):
        action_message = action_messages[-3]
        message = f"Including all exercises."
        if verbose_exercises_for_pc_steps:
            print(f"{action_message} {true_exercises_message} {message}")
        exercises_for_pc = get_exercises_for_pc_conditions(exercises, phase_component, 
                                                           conditions=[
                                                               exercise_has_valid_weights
                                                           ])

    if len(exercises_for_pc) < phase_component['exercises_per_bodypart_workout_min']:
        action_message = action_messages[-2]
        if verbose_exercises_for_pc_steps:
            print(f"{action_message:<{action_messages_max_length}} {true_exercises_message} {message}")
        message = f"No solution found."

    # Log whether other exercises needed to be included.
    if message and verbose_agent_preprocessing:
        print(f"{action_message:<{action_messages_max_length}} {true_exercises_message} {message}")
        if verbose_exercises_for_pc_steps:
            print("")

    # Log whether no exercises were found yet none were needed.
    elif phase_component['exercises_per_bodypart_workout_min'] == 0 and len(exercises_for_pc) == 0 and verbose_agent_preprocessing:
        action_message = action_messages[-1]
        true_exercises_message = f"{phase_component['pc_name']} had and needs NO exercises for bodypart '{phase_component['bodypart_name'].upper()}'."
        message = "None were required so no action was taken."
        print(f"{action_message:<{action_messages_max_length}} {true_exercises_message} {message}")

    true_exercise_indicators_for_pc = indicate_if_exercise_is_true(true_exercises_for_pc, exercises_for_pc, message)
    return exercises_for_pc, true_exercise_indicators_for_pc

# A method for retrieving the possible exercises for all phase components.
# This method removes exercises specific for a phase commponent from those that are allowed for a phase component without any true exercises.
def get_exercises_for_all_pcs(exercises, phase_components):
    number_of_possible_exercises = len(exercises)

    exercise_and_indicators_for_pcs = [
        get_exercises_for_pc(exercises, phase_component)
        for phase_component in phase_components
    ]

    exercises_for_pcs=[]
    true_exercise_indicators_for_pcs=[]
    for exercises_for_pc, true_exercise_indicators_for_pc in exercise_and_indicators_for_pcs:
        exercises_for_pcs.append(exercises_for_pc)
        true_exercise_indicators_for_pcs.append(true_exercise_indicators_for_pc)

    # All phase components that have every possible exercise applied to them.
    pc_indices_without_true_exercises = [
        i
        for i in range(len(exercises_for_pcs))
        if len(exercises_for_pcs[i]) == number_of_possible_exercises
    ]

    # Remove the exercises from the phase components without true exercises for minimum searching.
    for i in pc_indices_without_true_exercises:
        exercises_for_pc = exercises_for_pcs[i]
        # Compare to every other list of exercises that have true exercises.
        for j in range(len(exercises_for_pcs)):
            if j in pc_indices_without_true_exercises:
                continue
            exercises_for_pc = list(set(exercises_for_pc) - set(exercises_for_pcs[j]))
        if exercises_for_pc:
            exercises_for_pcs[i] = exercises_for_pc

    return exercises_for_pcs, true_exercise_indicators_for_pcs
