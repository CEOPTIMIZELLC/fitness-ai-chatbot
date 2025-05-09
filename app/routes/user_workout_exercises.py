import random
import heapq
import math

from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import (
    Exercise_Library, 
    Exercise_Component_Phases, 
    Phase_Library, 
    Phase_Component_Library, 
    Phase_Component_Bodyparts, 
    User_Exercises, 
    User_Weekday_Availability, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Workout_Exercises
)

bp = Blueprint('user_workout_exercises', __name__)

from app.agents.exercises import get_exercises_for_pc, get_exercises_for_all_pcs
from app.agents.exercises import Main as exercises_main
from app.agents.exercises_phase_components import Main as exercise_pc_main
from app.utils.common_table_queries import current_workout_day, user_possible_exercises_with_user_exercise_info
from app.utils.agent_pre_processing import retrieve_total_time_needed, check_if_there_is_enough_time



# ----------------------------------------- Workout Exercises -----------------------------------------

dummy_exercise = {
    "id": 0,
    "name": "Inactive",
    "base_strain": 0,
    "technical_difficulty": 0,
    "component_id": 0,
    "subcomponent_id": 0,
    "body_region_ids": None,
    "bodypart_ids": None,
    "muscle_group_ids": None,
    "muscle_ids": None
}

dummy_phase_component = {
    "id": 0,
    "name": "Inactive",
    "bodypart_name": "Inactive",
    "duration": 0,
    "duration_min": 0,
    "duration_min_max": 0,
    "duration_max": 0,
    "working_duration_min": 0,
    "working_duration_max": 0,
    'reps_min': 0, 
    'reps_max': 0, 
    'sets_min': 0, 
    'sets_max': 0, 
    'seconds_per_exercise': 0, 
    'intensity_min': 0, 
    'intensity_max': 0, 
    'rest_min': 0, 
    'rest_max': 0,
    'exercises_per_bodypart_workout_min': 0,
    'exercises_per_bodypart_workout_max': 0,
    'exercise_selection_note': None
}

def user_component_dict(workout, pc):
    """Format the user workout component data."""
    return {
        "workout_component_id": workout.id,
        "workout_day_id": workout.workout_day_id,
        "bodypart_id": workout.bodypart_id,
        "bodypart_name": workout.bodyparts.name,
        "duration": workout.duration,
        "phase_component_id": pc.id,
        "phase_id": pc.phase_id,
        "phase_name": pc.phases.name,
        "component_id": pc.component_id,
        "component_name": pc.components.name,
        "subcomponent_id": pc.subcomponent_id,
        "subcomponent_name": pc.subcomponents.name,
        "pc_ids": [pc.component_id, pc.subcomponent_id],
        "density_priority": pc.subcomponents.density,
        "volume_priority": pc.subcomponents.volume,
        "load_priority": pc.subcomponents.load,
        "name": pc.name,
        "reps_min": pc.reps_min, "reps_max": pc.reps_max,
        "sets_min": pc.sets_min,
        "sets_max": pc.sets_max,
        "tempo": pc.tempo,
        "seconds_per_exercise": pc.seconds_per_exercise,
        "intensity_min": pc.intensity_min,
        "intensity_max": pc.intensity_max,
        "rest_min": pc.rest_min // 5,                          # Adjusted so that rest is a multiple of 5.
        "rest_max": pc.rest_max // 5,                          # Adjusted so that rest is a multiple of 5.
        "duration_min": pc.duration_min,
        "duration_min_max": pc.duration_min,
        "duration_max": pc.duration_max,
        "working_duration_min": pc.working_duration_min,
        "working_duration_max": pc.working_duration_max,
        "volume_min": pc.volume_min,
        "volume_max": pc.volume_max,
        "density_min": int(pc.density_min * 100),              # Scaled up to avoid floating point errors from model.
        "density_max": int(pc.density_max * 100),              # Scaled up to avoid floating point errors from model.
        "exercises_per_bodypart_workout_min": pc.exercises_per_bodypart_workout_min if pc.exercises_per_bodypart_workout_min != None else 1,
        "exercises_per_bodypart_workout_max": pc.exercises_per_bodypart_workout_max,
        "exercise_selection_note": pc.exercise_selection_note,
    }

def exercise_dict(exercise, user_exercise):
    """Format the exercise data."""
    return {
        "id": exercise.id,
        "name": exercise.name.lower(),
        "base_strain": exercise.base_strain,
        "technical_difficulty": exercise.technical_difficulty,
        "component_ids": [component_phase.component_id for component_phase in exercise.component_phases],
        "subcomponent_ids": [component_phase.subcomponent_id for component_phase in exercise.component_phases],
        "pc_ids": [[component_phase.component_id, component_phase.subcomponent_id] for component_phase in exercise.component_phases],
        "body_region_ids": exercise.all_body_region_ids,
        "bodypart_ids": exercise.all_bodypart_ids,
        "muscle_group_ids": exercise.all_muscle_group_ids,
        "muscle_ids": exercise.all_muscle_ids,
        "supportive_equipment_ids": exercise.all_supportive_equipment,
        "assistive_equipment_ids": exercise.all_assistive_equipment,
        "weighted_equipment_ids": exercise.all_weighted_equipment,
        "is_weighted": exercise.is_weighted,
        "marking_equipment_ids": exercise.all_marking_equipment,
        "other_equipment_ids": exercise.all_other_equipment,
        "one_rep_max": int(user_exercise.one_rep_max * 100),                    # Scaled up to avoid floating point errors from model.
        "one_rep_load": int(user_exercise.one_rep_load * 100),                  # Scaled up to avoid floating point errors from model.
        "volume": int(user_exercise.volume * (100 * 100)),                      # Scaled up to avoid floating point errors from model.
        "density": int(user_exercise.density * 100),                            # Scaled up to avoid floating point errors from model.
        "intensity": int(user_exercise.intensity),
        "performance": int(user_exercise.performance * (100 * 100 * 100)),      # Scaled up to avoid floating point errors from model.
        "duration": user_exercise.duration,
        "working_duration": user_exercise.working_duration,
    }


def delete_old_user_workout_exercises(workout_day_id):
    db.session.query(User_Workout_Exercises).filter_by(workout_day_id=workout_day_id).delete()
    print("Successfully deleted")

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_exercises():
    # Retrieve all possible exercises with their component phases
    results = (
        db.session.query(
            Exercise_Library,
            User_Exercises, 
        )
        .join(User_Exercises, User_Exercises.exercise_id == Exercise_Library.id)
        .all()
    )

    possible_exercises_list = [dummy_exercise]

    for exercise, user_exercise in results:
        possible_exercises_list.append(exercise_dict(exercise, user_exercise))
    return possible_exercises_list

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_available_exercises():
    # Retrieve all possible exercises with their component phases
    results = user_possible_exercises_with_user_exercise_info(current_user.id)

    possible_exercises_list = [dummy_exercise]

    for exercise, user_exercise in results:
        possible_exercises_list.append(exercise_dict(exercise, user_exercise))
    return possible_exercises_list

def construct_user_workout_components_list(user_workout_components):
    user_workout_components_list = [dummy_phase_component]

    # Convert the query into a list of dictionaries, adding the information for the phase restrictions.
    for user_workout_component in user_workout_components:
        user_workout_components_list.append(user_component_dict(user_workout_component, user_workout_component.phase_components))
    
    return user_workout_components_list

# Find the correct minimum and maximum range for the minimum duration.
def correct_minimum_duration_for_phase_component(phase_components, possible_exercises):
    exercises_for_pcs = get_exercises_for_all_pcs(possible_exercises[1:], phase_components[1:])

    for phase_component, exercises_for_pc in zip(phase_components[1:], exercises_for_pcs):
        pc_exercises_duration = [possible_exercises[i]["duration"]# if not possible_exercises[i]["is_weighted"] else 0
                                 for i in exercises_for_pc
                                 #if not possible_exercises[i]["is_weighted"]
                                 ]
        if pc_exercises_duration == []:
            min_exercise_duration_min = 0
            min_exercise_duration_max = 0
        else:
            min_exercise_duration_min = heapq.nsmallest((phase_component["exercises_per_bodypart_workout_min"] or 1), pc_exercises_duration)[-1]# + 1
            min_exercise_duration_max = heapq.nsmallest((phase_component["exercises_per_bodypart_workout_max"] or 1), pc_exercises_duration)[-1]# + 1
            min_exercise_duration = heapq.nsmallest((phase_component["exercises_per_bodypart_workout_max"] or 1), pc_exercises_duration)

        phase_component["duration_min"] = max(min_exercise_duration_min, phase_component["duration_min"])
        phase_component["duration_min_max"] = max(min_exercise_duration_max, phase_component["duration_min_max"])

    return None

def check_if_there_are_enough_exercises(phase_components, possible_exercises):
    exercises_for_pcs = get_exercises_for_all_pcs(possible_exercises[1:], phase_components[1:])

    return [{"phase_component_id": phase_component["phase_component_id"], "name": phase_component["name"], 
             "bodypart_id": phase_component["bodypart_id"], "bodypart_name": phase_component["bodypart_name"], 
             "number_of_exercises_needed": phase_component["exercises_per_bodypart_workout_min"], 
             "number_of_exercises_available": len(exercises_for_pc)}
             for phase_component, exercises_for_pc in zip(phase_components[1:], exercises_for_pcs)
             if phase_component["exercises_per_bodypart_workout_min"] > len(exercises_for_pc)]

def retrieve_pc_parameters(parameters, user_workout_day):
    # Retrieve user components
    user_workout_components = user_workout_day.workout_components

    if not user_workout_components:
        return jsonify({"status": "success", "exercises": "This phase component is inactive. No exercises for today."}), 200

    projected_duration = 0

    # Get the total desired duration.
    for user_workout_component in user_workout_components:
        projected_duration += user_workout_component.duration

    availability = (
        User_Weekday_Availability.query
        .filter_by(user_id=current_user.id, weekday_id=user_workout_day.weekday_id)
        .first())
    if not availability:
        return jsonify({"status": "error", "message": "No active weekday availability found."}), 404

    parameters["projected_duration"] = projected_duration
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = int(availability.availability.total_seconds())
    parameters["possible_exercises"] = retrieve_available_exercises()

    # Change the minimum allowed duration if the exercises possible don't allow for it.
    correct_minimum_duration_for_phase_component(parameters["phase_components"], parameters["possible_exercises"])
    return parameters

def agent_output_to_sqlalchemy_model(exercises_output, workout_day_id):
    new_exercises = []
    for i, exercise in enumerate(exercises_output, start=1):
        # Create a new exercise entry.
        new_exercise = User_Workout_Exercises(
            workout_day_id = workout_day_id,
            phase_component_id = exercise["phase_component_id"],
            exercise_id = exercise["exercise_id"],
            #bodypart_id = exercise["bodypart_id"],
            order = i,
            reps = exercise["reps_var"],
            sets = exercise["sets_var"],
            intensity = exercise["intensity_var"],
            rest = exercise["rest_var"],
            weight = exercise["training_weight"],
        )

        new_exercises.append(new_exercise)
    return new_exercises


# Retrieve current user's workout exercises
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_exercises_list():
    user_workout_exercises = (
        User_Workout_Exercises.query
        .join(User_Workout_Days)
        .join(User_Microcycles)
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter_by(user_id=current_user.id)
        .all())

    result = []
    for user_workout_exercise in user_workout_exercises:
        result.append(user_workout_exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Retrieve user's current microcycle's workout exercises
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_exercises_list():
    result = []
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    user_workout_exercises = user_workout_day.exercises
    for user_workout_exercise in user_workout_exercises:
        result.append(user_workout_exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Assigns exercises to workouts.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def exercise_initializer():

    parameters={}
    constraints={}

    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    delete_old_user_workout_exercises(user_workout_day.id)

    parameters = retrieve_pc_parameters(parameters, user_workout_day)

    maximum_min_duration = max(item["duration_min"] for item in parameters["phase_components"][1:])
    total_time_needed = retrieve_total_time_needed(parameters["phase_components"][1:], "exercises_per_bodypart_workout_min")

    # Check if there is enough time to complete the phase components.
    not_enough_time_message = check_if_there_is_enough_time(total_time_needed, parameters["availability"], maximum_min_duration)
    if not_enough_time_message:
        return jsonify({"status": "error", "message": not_enough_time_message}), 400

    # Check if there are enough exercises to complete the phase components.
    phase_components_without_enough_exercises = check_if_there_are_enough_exercises(parameters["phase_components"], parameters["possible_exercises"])
    if phase_components_without_enough_exercises:
        pc_without_enough_ex_message = [
            f"{pc_without_enough_ex["name"]} requires a minimum of {pc_without_enough_ex["number_of_exercises_needed"]} to be successful but only has {pc_without_enough_ex["number_of_exercises_available"]}"
            for pc_without_enough_ex in phase_components_without_enough_exercises]
        return jsonify({"status": "error", "message": pc_without_enough_ex_message}), 400

    result = []
    result = exercises_main(parameters, constraints)
    output = result["output"]
    print(result["formatted"])

    user_workout_exercises = agent_output_to_sqlalchemy_model(output, user_workout_day.id)

    db.session.add_all(user_workout_exercises)
    db.session.commit()

    return jsonify({"status": "success", "exercises": result}), 200

# Update user exercises if workout is completed.
@bp.route('/workout_completed', methods=['POST', 'PATCH'])
@login_required
def complete_workout():
    result = []
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404
    workout_exercises = user_workout_day.exercises

    for exercise in workout_exercises:
        user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise.exercise_id})

        new_weight = exercise.weight or 0

        new_one_rep_max = round((new_weight * (30 + exercise.reps)) / 30, 2)

        # Only replace if the new one rep max is larger.
        user_exercise.one_rep_max = max(user_exercise.one_rep_max, new_one_rep_max)
        user_exercise.one_rep_load = new_one_rep_max
        user_exercise.volume = exercise.volume
        user_exercise.density = exercise.density
        user_exercise.intensity = exercise.intensity
        user_exercise.duration = exercise.duration
        user_exercise.working_duration = exercise.working_duration

        # Only replace if the new performance is larger.
        user_exercise.performance = max(user_exercise.performance, exercise.performance)

        db.session.commit()

        result.append(user_exercise.to_dict())

    return jsonify({"status": "success", "user_exercises": result}), 200

# Combine Exercise Initializer and Complete Workout for testing.
@bp.route('/initialize_and_complete', methods=['POST', 'PATCH'])
@login_required
def initialize_and_complete():
    result = {}
    exercise_initializer_result = exercise_initializer()
    # Return error if nothing is found.
    if exercise_initializer_result[1] == 404:
        return exercise_initializer_result
    complete_workout_result = complete_workout()

    # Return error if nothing is found.
    if complete_workout_result[1] == 404:
        return complete_workout_result
    result["user_workout_exercises"] = exercise_initializer_result[0].get_json()["exercises"]["output"]
    result["user_exercises"] = complete_workout_result[0].get_json()["user_exercises"]
    return jsonify({"status": "success", "output": result}), 200

# This is simply for the purposes of testing the phase component assignment stage.
@bp.route('/test_exercise_phase_components', methods=['POST', 'PATCH'])
@login_required
def exercise_phase_components_test():
    parameters={}
    constraints={}

    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active workout day found."}), 404

    parameters = retrieve_pc_parameters(parameters, user_workout_day)

    result = []
    result = exercise_pc_main(parameters, constraints)
    print(result["formatted"])

    return jsonify({"status": "success", "exercises": result}), 200
