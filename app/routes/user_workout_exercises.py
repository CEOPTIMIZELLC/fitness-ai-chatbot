import random
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

from app.agents.exercises import Main as exercises_main
from app.utils.common_table_queries import current_workout_day

# ----------------------------------------- Phase_Components -----------------------------------------

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

def user_component_dict(workout, phase_component):
    """Format the user workout component data."""
    return {
        "workout_component_id": workout.id,
        "workout_day_id": workout.workout_day_id,
        "bodypart_id": workout.bodypart_id,
        "bodypart_name": workout.bodyparts.name,
        "duration": workout.duration,
        "phase_component_id": phase_component.id,
        "phase_name": phase_component.phases.name,
        "component_id": phase_component.component_id,
        "component_name": phase_component.components.name,
        "subcomponent_id": phase_component.subcomponent_id,
        "subcomponent_name": phase_component.subcomponents.name,
        "density_priority": phase_component.subcomponents.density,
        "volume_priority": phase_component.subcomponents.volume,
        "load_priority": phase_component.subcomponents.load,
        "name": phase_component.name,
        "reps_min": phase_component.reps_min,
        "reps_max": phase_component.reps_max,
        "sets_min": phase_component.sets_min,
        "sets_max": phase_component.sets_max,
        "tempo": phase_component.tempo,
        "seconds_per_exercise": phase_component.seconds_per_exercise,
        "intensity_min": phase_component.intensity_min,
        "intensity_max": phase_component.intensity_max,
        "rest_min": phase_component.rest_min // 5,                          # Adjusted so that rest is a multiple of 5.
        "rest_max": phase_component.rest_max // 5,                          # Adjusted so that rest is a multiple of 5.
        "duration_min": phase_component.duration_min,
        "duration_max": phase_component.duration_max,
        "working_duration_min": phase_component.working_duration_min,
        "working_duration_max": phase_component.working_duration_max,
        "volume_min": phase_component.volume_min,
        "volume_max": phase_component.volume_max,
        "density_min": int(phase_component.density_min * 100),              # Scaled up to avoid floating point errors from model.
        "density_max": int(phase_component.density_max * 100),              # Scaled up to avoid floating point errors from model.
        "exercises_per_bodypart_workout_min": phase_component.exercises_per_bodypart_workout_min,
        "exercises_per_bodypart_workout_max": phase_component.exercises_per_bodypart_workout_max,
        "exercise_selection_note": phase_component.exercise_selection_note,
    }

def exercise_dict(exercise, user_exercise, phase):
    """Format the exercise data."""
    return {
        "id": exercise.id,
        "name": exercise.name.lower(),
        "base_strain": exercise.base_strain,
        "technical_difficulty": exercise.technical_difficulty,
        "component_id": phase.component_id,
        "subcomponent_id": phase.subcomponent_id,
        "body_region_ids": exercise.all_body_region_ids,
        "bodypart_ids": exercise.all_bodypart_ids,
        "muscle_group_ids": exercise.all_muscle_group_ids,
        "muscle_ids": exercise.all_muscle_ids,
        "supportive_equipment_ids": exercise.all_supportive_equipment,
        "assistive_equipment_ids": exercise.all_assistive_equipment,
        "weighted_equipment_ids": exercise.all_weighted_equipment,
        "marking_equipment_ids": exercise.all_marking_equipment,
        "other_equipment_ids": exercise.all_other_equipment,
        "one_rep_max": int(user_exercise.one_rep_max * 100),                    # Scaled up to avoid floating point errors from model.
        "one_rep_load": int(user_exercise.one_rep_load * 100),                  # Scaled up to avoid floating point errors from model.
        "volume": int(user_exercise.volume * (100 * 100)),                      # Scaled up to avoid floating point errors from model.
        "density": int(user_exercise.density * 100),                            # Scaled up to avoid floating point errors from model.
        "intensity": int(user_exercise.intensity),
        "performance": int(user_exercise.performance * (100 * 100 * 100)),      # Scaled up to avoid floating point errors from model.
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
            Exercise_Component_Phases,
        )
        .join(Exercise_Component_Phases, Exercise_Library.id == Exercise_Component_Phases.exercise_id)
        .join(User_Exercises, User_Exercises.exercise_id == Exercise_Library.id)
        .all()
    )

    possible_exercises_list = [dummy_exercise]

    for exercise, user_exercise, phase in results:
        possible_exercises_list.append(exercise_dict(exercise, user_exercise, phase))
    return possible_exercises_list

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_available_exercises():
    from app.utils.common_table_queries import user_available_exercises_with_user_exercise_info

    # Retrieve all possible exercises with their component phases
    results = user_available_exercises_with_user_exercise_info(current_user.id)

    possible_exercises_list = [dummy_exercise]

    for exercise, user_exercise, phase in results:
        possible_exercises_list.append(exercise_dict(exercise, user_exercise, phase))
    return possible_exercises_list

def construct_user_workout_components_list(user_workout_components):
    user_workout_components_list = [dummy_phase_component]

    # Convert the query into a list of dictionaries, adding the information for the phase restrictions.
    for user_workout_component in user_workout_components:
        user_workout_components_list.append(user_component_dict(user_workout_component, user_workout_component.phase_components))
    
    return user_workout_components_list


def retrieve_duration_for_test(duration_min, exercise_min=1, exercises_max=1):
    exercises_per_bodypart = random.randint(exercise_min, exercises_max)
    duration = exercises_per_bodypart * duration_min
    return duration

def construct_user_workout_components_list_for_test(possible_phase_components, possible_phase_component_bodyparts, availability, projected_duration):
    workout_component_id = 0
    user_workout_components_list = [dummy_phase_component]

    # Convert the query into a list of dictionaries, adding the information for the phase restrictions.
    for possible_phase_component in possible_phase_components:
        # workout_data = user_workout_component.to_dict()
        phase_component_data = possible_phase_component.to_dict()
        exercises_per_bodypart_min = phase_component_data["exercises_per_bodypart_workout_min"] or 1
        exercises_per_bodypart_max = phase_component_data["exercises_per_bodypart_workout_max"] or 1

        # If the phase component is resistance, append it multiple times.
        if possible_phase_component.component_id == 6:
            for possible_phase_component_bodypart in possible_phase_component_bodyparts:
                duration = retrieve_duration_for_test(phase_component_data["duration_min"], exercises_per_bodypart_min, exercises_per_bodypart_max)

                if duration <= availability:
                    workout_component_id += 1
                    availability -= duration
                    projected_duration += duration
                    user_workout_components_list.append(user_component_dict(
                        {
                            "id": workout_component_id,
                            "workout_day_id": 0,
                            "bodypart_id": possible_phase_component_bodypart.bodypart_id,
                            "bodypart_name": possible_phase_component_bodypart.bodyparts.name,
                            "duration": duration
                        },
                        phase_component_data))
        # Append only once for full body if any other phase component.
        else:
            duration = retrieve_duration_for_test(phase_component_data["duration_min"], exercises_per_bodypart_min, exercises_per_bodypart_max)
            if duration <= availability:
                workout_component_id += 1
                availability -= duration
                projected_duration += duration
                user_workout_components_list.append(user_component_dict(
                    {
                        "id": workout_component_id,
                        "workout_day_id": 0,
                        "bodypart_id": 1,
                        "bodypart_name": "total_body",
                        "duration": duration
                    },
                    phase_component_data
                ))
    return user_workout_components_list, availability, projected_duration


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
            intensity = 0,
            rest = exercise["rest_var"]
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

    delete_old_user_workout_exercises(user_workout_day.id)

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

    parameters["projected_duration"] = projected_duration
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = int(availability.availability.total_seconds())
    parameters["workout_length"] = int(current_user.workout_length.total_seconds())
    parameters["possible_exercises"] = retrieve_exercises()

    result = []
    result = exercises_main(parameters, constraints)
    output = result["output"]
    print(result["formatted"])

    user_workout_exercises = agent_output_to_sqlalchemy_model(output, user_workout_day.id)

    db.session.add_all(user_workout_exercises)
    db.session.commit()

    for exercise in output:
        user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise["exercise_id"]})

        new_one_rep_max = round((exercise["training_weight"] * (30 + exercise["reps_var"])) / 30, 2)

        # Only replace if the new one rep max is larger.
        user_exercise.one_rep_max = max(user_exercise.one_rep_max, new_one_rep_max)
        user_exercise.one_rep_load = new_one_rep_max
        user_exercise.volume = exercise["volume"]
        user_exercise.density = exercise["density"]
        user_exercise.intensity = exercise["intensity_var"]

        # Only replace if the new performance is larger.
        user_exercise.performance = max(user_exercise.performance, exercise["performance"])

        db.session.commit()

    return jsonify({"status": "success", "exercises": result}), 200


# Testing for the parameter programming for mesocycle labeling.
@bp.route('/test', methods=['GET', 'POST'])
def exercise_classification_test():
    from app.routes.user_workout_days import retrieve_possible_phase_components, retrieve_phase_component_bodyparts

    test_results = []

    parameters={}
    constraints={}

    # Retrieve all possible phases.
    phases = (
        db.session.query(Phase_Library.id)
        .group_by(Phase_Library.id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    parameters["availability"] = 50 * 60
    parameters["workout_length"] = 30 * 60
    parameters["one_rep_max_improvement_percentage"] = 25

    for phase in phases:
        while True:
            availability = min(parameters["availability"], parameters["workout_length"])
            projected_duration = 0

            # Retrieve all possible phase component body parts.
            possible_phase_component_bodyparts = retrieve_phase_component_bodyparts(phase.id)

            # Retrieve all possible phase components that can be selected for the phase id.
            possible_phase_components = retrieve_possible_phase_components(phase.id)
            possible_phase_components_list, availability, projected_duration = construct_user_workout_components_list_for_test(
                possible_phase_components, 
                possible_phase_component_bodyparts,
                availability,
                projected_duration)

            # Adding the condition break after ensures the loop runs at least once.
            if not (availability > 120):
                break


        parameters["projected_duration"] = projected_duration
        parameters["phase_components"] = possible_phase_components_list
        parameters["possible_exercises"] = retrieve_exercises()

        print(str(phase.id))
        result = exercises_main(parameters, constraints)
        print(result["formatted"])
        test_results.append({
            "projected_duration": parameters["projected_duration"],
            "workout_length": parameters["workout_length"],
            "availability": parameters["availability"],
            "phase_id": phase.id,
            "result": result
        })

        print("----------------------")

    return jsonify({"status": "success", "test_results": test_results}), 200