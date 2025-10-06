from flask import abort

from app.construct_lists_from_sql.exercises import Main as construct_available_exercises_list
from app.construct_lists_from_sql.general_exercises import Main as construct_available_general_exercises_list
from app.construct_lists_from_sql.user_workout_components import construct_user_workout_components_list
from app.altering_agents.utils.agent_pre_processing import *

# ----------------------------------------- Workout Exercises -----------------------------------------

# Verifies and updates the phase component information.
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_phase_component_information(parameters, pcs, exercises):
    # Retrieve parameters. Returned information includes the phase components, exercises, and exercises for phase components.
    pcs, exercises = verify_pc_information(parameters, pcs, exercises, parameters["availability"], "duration_min", "exercises_per_bodypart_workout_min", check_globally=True)
    
    pcs_new = [pc for pc in pcs if pc.get("allowed_exercises")]

    # Replace the ends of both lists with the corrected versions. 
    parameters["phase_components"][1:] = pcs_new
    parameters["possible_exercises"][1:] = exercises
    return None

# Retrieves the total projected duration for the workout. 
# Updates the projected duration to be the maximum allowed time given the exercises available if this would be lower.
def retrieve_projected_duration(user_workout_components, pcs):
    # Get the total desired duration.
    projected_duration = 0
    for user_workout_component in user_workout_components:
        projected_duration += user_workout_component["duration"]

    # If the maximum possible duration is larger than the projected duration, lower the projected duration to be this maximum.
    max_time_possible = retrieve_total_time_needed(pcs, "duration_max", "exercises_per_bodypart_workout_max")
    return min(max_time_possible, projected_duration)

# Retrieves the parameters used by the solver.
# Information included:
#   The length allowed for the workout.
#   The projected duration of the workout.
#   The phase component information relevant for the workout.
#   The exercises that can be assigned in the workout.
def retrieve_parameters(user_id, user_workout_day, availability):
    parameters = {"valid": True, "status": None}

    # Retrieve user components
    user_workout_components = user_workout_day.workout_components
    if not user_workout_components:
        abort(400, description="This phase component is inactive. No exercises for today.")

    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = availability
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["possible_exercises"] = construct_available_exercises_list(user_id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_phase_component_information(parameters, parameters["phase_components"][1:], parameters["possible_exercises"][1:])

    parameters["projected_duration"] = retrieve_projected_duration(parameters["phase_components"][1:], parameters["phase_components"][1:])
    return parameters