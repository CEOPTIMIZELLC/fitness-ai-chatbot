from flask import jsonify, Blueprint
from flask_login import current_user, login_required

from app import db
from app.models import Exercise_Library, Exercise_Component_Phases, Phase_Library, Phase_Component_Library, Phase_Component_Bodyparts, User_Weekday_Availability, User_Macrocycles, User_Mesocycles, User_Microcycles, User_Workout_Days, User_Exercises

bp = Blueprint('user_exercises', __name__)

from app.agents.exercises import Main as exercises_main
from app.helper_functions.common_table_queries import current_workout_day

# ----------------------------------------- Phase_Components -----------------------------------------

def delete_old_user_exercises(workout_day_id):
    db.session.query(User_Exercises).filter_by(workout_day_id=workout_day_id).delete()
    print("Successfully deleted")

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_possible_phase_components(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_components = (
        Phase_Component_Library.query
        .join(Phase_Library)
        .filter(Phase_Library.id == phase_id)
        .order_by(Phase_Component_Library.id.asc())
        .all()
    )
    return possible_phase_components

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_component_bodyparts(phase_id):
    # Retrieve all possible phase components that can be selected.
    possible_phase_component_bodyparts = (
        Phase_Component_Bodyparts.query
        .filter(Phase_Component_Bodyparts.phase_id == phase_id)
        .order_by(Phase_Component_Bodyparts.id.asc())
        .all()
    )
    return possible_phase_component_bodyparts

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_exercises():
    # Retrieve all possible exercises that can be selected.
    results = (
        db.session.query(Exercise_Library, Exercise_Component_Phases)
        .join(Exercise_Component_Phases, Exercise_Library.id == Exercise_Component_Phases.exercise_id)
        .order_by(Exercise_Library.id.asc())
        .all())

    possible_exercises_list = [
        {
            "id": exercise.id,
            "name": exercise.name.lower(),
            "base_strain": exercise.base_strain,
            "technical_difficulty": exercise.technical_difficulty,
            "component_id": phase.component_id,
            "subcomponent_id": phase.subcomponent_id,
        }
        for exercise, phase in results
    ]

    return possible_exercises_list

def construct_user_workout_components_list(user_workout_components):
    user_workout_components_list = [{
        "id": 0,
        "name": "Inactive",
        "bodypart_name": "Inactive",
        "duration": 0,
        "duration_min": 0,
        "duration_max": 0,
        'reps_min': 0, 
        'reps_max': 0, 
        'sets_min': 0, 
        'sets_max': 0, 
        'seconds_per_exercise': 0, 
        'intensity_min': 0, 
        'intensity_max': 0, 
        'rest_min': 0, 
        'rest_max': 0
    }]

    # Convert the query into a list of dictionaries, adding the information for the phase restrictions.
    for user_workout_component in user_workout_components:
        workout_data = user_workout_component.to_dict()
        phase_component_data = user_workout_component.phase_components.to_dict()

        user_workout_components_list.append({
            "workout_component_id": workout_data["id"],
            "workout_day_id": workout_data["workout_day_id"],
            "bodypart_id": workout_data["bodypart_id"],
            "bodypart_name": workout_data["bodypart_name"],
            "duration": workout_data["duration"],
            "duration_min": (
                (phase_component_data["exercises_per_bodypart_workout_min"] or 1)
                * (phase_component_data["seconds_per_exercise"] * phase_component_data["reps_min"] + phase_component_data["rest_min"]) 
                * phase_component_data["sets_min"]
            ),
            "duration_max": (
                (phase_component_data["exercises_per_bodypart_workout_max"] or 1)
                * (phase_component_data["seconds_per_exercise"] * phase_component_data["reps_max"] + phase_component_data["rest_max"]) 
                * phase_component_data["sets_max"]),

            "phase_component_id": phase_component_data["id"],
            "phase_name": phase_component_data["phase_name"],
            "component_name": phase_component_data["component_name"],
            "name": phase_component_data["name"],
            "reps_min": phase_component_data["reps_min"],
            "reps_max": phase_component_data["reps_max"],
            "sets_min": phase_component_data["sets_min"],
            "sets_max": phase_component_data["sets_max"],
            "tempo": phase_component_data["tempo"],
            "seconds_per_exercise": phase_component_data["seconds_per_exercise"],
            "intensity_min": phase_component_data["intensity_min"],
            "intensity_max": phase_component_data["intensity_max"],
            "rest_min": phase_component_data["rest_min"] // 5,     # Adjusted so that rest is a multiple of 5.
            "rest_max": phase_component_data["rest_max"] // 5,     # Adjusted so that rest is a multiple of 5.
            "exercises_per_bodypart_workout_min": phase_component_data["exercises_per_bodypart_workout_min"],
            "exercises_per_bodypart_workout_max": phase_component_data["exercises_per_bodypart_workout_max"],
            "exercise_selection_note": phase_component_data["exercise_selection_note"],
  
        })
    
    return user_workout_components_list

def agent_output_to_sqlalchemy_model(exercises_output, user_workdays):
    new_exercises = []
    for exercise in exercises_output:
        # Create a new exercise entry.
        new_exercise = User_Exercises(
            #exercise_id = exercise["exercise_id"],
            bodypart_id = exercise["bodypart_id"],
            order = 0,
            reps = exercise["reps_var"],
            sets = exercise["sets_var"],
            intensity = 0,
            rest = exercise["rest_var"],
            exercises_per_bodypart = exercise["bodypart_var"]
        )

        new_exercises.append(new_exercise)
    return user_workdays


# Retrieve phase components
@bp.route('/', methods=['GET'])
@login_required
def get_user_exercises():
    user_exercises = User_Exercises.query.join(User_Workout_Days).join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_exercise in user_exercises:
        result.append(user_exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Retrieve phase components
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_exercises():
    result = []
    user_workout_day = current_workout_day(current_user.id)
    user_exercises = user_workout_day.exercises
    for user_exercise in user_exercises:
        result.append(user_exercise.to_dict())
    return jsonify({"status": "success", "exercises": result}), 200

# Assigns exercises to workouts.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def exercise_initializer():

    parameters={}
    constraints={}

    user_workout_day = current_workout_day(current_user.id)

    delete_old_user_exercises(user_workout_day.id)

    # Retrieve user components
    user_workout_components = user_workout_day.workout_components

    if not user_workout_components:
        return jsonify({"status": "success", "exercises": "This phase component is inactive. No exercises for today."}), 200

    projected_duration = 0

    # Get the total desired duration.
    for user_workout_component in user_workout_components:
        projected_duration += user_workout_component.duration
    user_workout_components_list = construct_user_workout_components_list(user_workout_components)

    # Retrieve all possible phase components that can be selected for the phase id.
    #possible_phase_components = retrieve_possible_phase_components(user_workout_day.microcycles.mesocycles.phase_id)

    availability = (
        User_Weekday_Availability.query
        .filter_by(user_id=current_user.id, weekday_id=user_workout_day.weekday_id)
        .first())

    parameters["projected_duration"] = projected_duration
    parameters["phase_components"] = user_workout_components_list
    parameters["availability"] = int(availability.availability.total_seconds())
    parameters["workout_length"] = int(current_user.workout_length.total_seconds())

    possible_exercises = retrieve_exercises()

    result = []
    result = exercises_main(parameters, constraints)
    print(result["formatted"])

    # user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)

    # db.session.add_all(user_workdays)
    # db.session.commit()

    return jsonify({"status": "success", "exercises": result}), 200