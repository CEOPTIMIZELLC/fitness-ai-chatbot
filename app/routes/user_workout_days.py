from config import verbose
from flask import jsonify, Blueprint
from flask_login import current_user, login_required
import math

from app import db
from app.models import Phase_Library, Phase_Component_Library, Phase_Component_Bodyparts, Weekday_Library, User_Weekday_Availability, User_Workout_Components, User_Macrocycles, User_Mesocycles, User_Microcycles, User_Workout_Days
from datetime import timedelta

bp = Blueprint('user_workout_days', __name__)

from app.agents.phase_components import Main as phase_component_main
from app.utils.common_table_queries import current_microcycle, current_workout_day, user_possible_exercises_with_user_exercise_info
from app.routes.utils import retrieve_total_time_needed, check_if_there_is_enough_time
from app.utils.get_all_exercises_for_pc import get_exercises_for_all_pcs

from app.routes.utils import correct_minimum_duration_for_phase_component, check_if_there_are_enough_exercises, correct_maximum_allowed_exercises_for_phase_component
from app.routes.utils import construct_available_exercises_list, construct_phase_component_list
# ----------------------------------------- Workout Days -----------------------------------------

def delete_old_user_workout_days(microcycle_id):
    db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
    if verbose:
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

# Given a start date and a duration, convert into a list of weekdays and create a corresponding workout day entry.
def duration_to_weekdays(dur, start_date, microcycle_id):
    microcycle_weekdays = []
    user_workdays = []

    start_date_number = start_date.weekday()

    # Loop through the number of iterations
    for i in range(dur):
        # Calculate the current number using modulo to handle the circular nature
        weekday_number = (start_date_number + i) % 7
        microcycle_weekdays.append(weekday_number)

        new_workday = User_Workout_Days(
            microcycle_id = microcycle_id,
            weekday_id = weekday_number,
            order = i+1,
            date = (start_date + timedelta(days=i))
        )
        user_workdays.append(new_workday)
    
    return microcycle_weekdays, user_workdays

# Verifies and updates the phase component information.
# Updates the lower bound for duration if the user's current performance for all exercises in a phase component requires a higher minimum.
# Checks if the minimum amount of exercises allowed could fit into the workout with the current duration. 
# Checks if there are enough exercises to meet the minimum amount of exercises for a phase component. 
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_phase_component_information(parameters, pcs, exercises):
    exercises_for_pcs = get_exercises_for_all_pcs(exercises, pcs)

    # Change the minimum allowed duration if the exercises possible don't allow for it.
    correct_minimum_duration_for_phase_component(pcs, parameters["possible_exercises"], exercises_for_pcs)

    # Check if there are enough exercises to complete the phase components.
    pc_without_enough_ex_message = check_if_there_are_enough_exercises(pcs, exercises_for_pcs)
    if pc_without_enough_ex_message:
        return jsonify({"status": "error", "message": pc_without_enough_ex_message}), 400

    correct_maximum_allowed_exercises_for_phase_component(pcs, exercises_for_pcs)
    return None

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters={}
    constraints={}

    # Retrieve all possible phase component body parts.
    possible_phase_component_bodyparts = retrieve_phase_component_bodyparts(phase_id)

    # Retrieve all possible phase components that can be selected for the phase id.
    possible_phase_components = retrieve_possible_phase_components(phase_id)
    possible_phase_components_list = construct_phase_component_list(possible_phase_components, possible_phase_component_bodyparts)

    maximum_min_duration = max(item["duration_min"] for item in possible_phase_components_list)
    total_time_needed = retrieve_total_time_needed(possible_phase_components_list, "duration_min", "frequency_per_microcycle_min", number_of_available_weekdays)

    # Check if there is enough time to complete the phase components.
    not_enough_time_message = check_if_there_is_enough_time(total_time_needed, total_availability, maximum_min_duration)
    if not_enough_time_message:
        return {"status": "output", "message": not_enough_time_message}

    parameters["microcycle_weekdays"] = microcycle_weekdays
    parameters["weekday_availability"] = weekday_availability
    parameters["phase_components"] = possible_phase_components_list
    exercises_with_component_phases = user_possible_exercises_with_user_exercise_info(current_user.id)
    parameters["possible_exercises"] = construct_available_exercises_list(exercises_with_component_phases)

    pc_verification_message = verify_phase_component_information(parameters, parameters["phase_components"], parameters["possible_exercises"][1:])
    if pc_verification_message:
        return pc_verification_message


    result = phase_component_main(parameters, constraints)
    if verbose:
        print(result["formatted"])
    return result

def agent_output_to_sqlalchemy_model(phase_components_output, user_workdays):
    for phase_component in phase_components_output:
        # Create a new component entry.
        new_component = User_Workout_Components(
            phase_component_id = phase_component["phase_component_id"],
            bodypart_id = phase_component["bodypart_id"],
            duration = phase_component["duration_var"]
        )

        # Append the component to its corresponding workday.
        user_workdays[phase_component["workday_index"]].workout_components.append(new_component)
    return user_workdays

# Retrieve current user's phase components
@bp.route('/', methods=['GET'])
@login_required
def get_user_workout_days_list():
    user_workout_days = User_Workout_Days.query.join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
    result = []
    for user_workout_day in user_workout_days:
        result.append(user_workout_day.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve user's current microcycle's phase components
@bp.route('/current_list', methods=['GET'])
@login_required
def get_user_current_workout_days_list():
    result = []
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active microcycle found."}), 404
    user_workout_days = user_microcycle.workout_days
    for user_workout_day in user_workout_days:
        result.append(user_workout_day.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Retrieve user's current phase component
@bp.route('/current', methods=['GET'])
@login_required
def read_user_current_workout_day():
    user_workout_day = current_workout_day(current_user.id)
    if not user_workout_day:
        return jsonify({"status": "error", "message": "No active phase component found."}), 404
    return jsonify({"status": "success", "phase_components": user_workout_day.to_dict()}), 200

# Assigns phase components to days along with projected length.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer():
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active microcycle found."}), 404

    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == current_user.id)
        .order_by(User_Weekday_Availability.user_id.asc())
        .all())
    if not availability:
        return jsonify({"status": "error", "message": "No active weekday availability found."}), 404

    delete_old_user_workout_days(user_microcycle.id)
    microcycle_weekdays, user_workdays = duration_to_weekdays(user_microcycle.duration.days, user_microcycle.start_date, user_microcycle.id)

    weekday_availability = []

    number_of_available_weekdays = 0
    total_availability = 0
    for day in availability:
        weekday_availability.append({
            "id": day.weekday_id, 
            "name": day.weekdays.name.title(), 
            "availability": int(day.availability.total_seconds())
        })
        total_availability += day.availability.total_seconds()
        if day.availability.total_seconds() > 0:
            number_of_available_weekdays += 1

    result = perform_workout_day_selection(user_microcycle.mesocycles.phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)
    if result["output"] == "error":
        return jsonify({"status": "error", "message": result["message"]}), 404

    user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)
    db.session.add_all(user_workdays)
    db.session.commit()

    return jsonify({"status": "success", "workdays": result}), 200

# Assigns phase components to days along with projected length.
@bp.route('/<phase_id>', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer_by_id(phase_id):
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active microcycle found."}), 404

    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == current_user.id)
        .order_by(User_Weekday_Availability.user_id.asc())
        .all())
    if not availability:
        return jsonify({"status": "error", "message": "No active weekday availability found."}), 404

    delete_old_user_workout_days(user_microcycle.id)
    microcycle_weekdays, user_workdays = duration_to_weekdays(user_microcycle.duration.days, user_microcycle.start_date, user_microcycle.id)

    weekday_availability = []

    number_of_available_weekdays = 0
    total_availability = 0
    for day in availability:
        weekday_availability.append({
            "id": day.weekday_id, 
            "name": day.weekdays.name.title(), 
            "availability": int(day.availability.total_seconds())
        })
        total_availability += day.availability.total_seconds()
        if day.availability.total_seconds() > 0:
            number_of_available_weekdays += 1

    result = perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)
    if result["output"] == "error":
        return jsonify({"status": "error", "message": result["message"]}), 404

    user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)
    db.session.add_all(user_workdays)
    db.session.commit()

    return jsonify({"status": "success", "workdays": result}), 200

# Testing for the parameter programming for phase component assignment.
@bp.route('/test/<phase_id>', methods=['GET', 'POST'])
def test_workout_day_by_id(phase_id):
    weekday_availability_temp = [
        {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
        {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
        {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
        {"id": 3, "name": "Thursday", "availability": 35 * 60},
        {"id": 4, "name": "Friday", "availability": 0 * 60 * 60},
        {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
        {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
    ]
    microcycle_weekdays =  [0, 1, 2, 3, 4, 5, 6]
    weekday_availability = []

    number_of_available_weekdays = 0
    total_availability = 0
    for day in microcycle_weekdays:
        availability = weekday_availability_temp[day]["availability"]
        weekday_availability.append({
            "id": weekday_availability_temp[day]["id"], 
            "name": weekday_availability_temp[day]["name"].title(), 
            "availability": availability
        })
        total_availability += availability
        if availability > 0:
            number_of_available_weekdays += 1

    result = perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)

    return jsonify({"status": "success", "mesocycles": result}), 200

# Testing for the parameter programming for phase component assignment.
@bp.route('/test', methods=['GET', 'POST'])
def phase_component_classification_test():
    test_results = []

    weekday_availability_temp = [
        {"id": 0, "name": "Monday", "availability": 6 * 60 * 60},
        {"id": 1, "name": "Tuesday", "availability": 3 * 60 * 60},
        {"id": 2, "name": "Wednesday", "availability": 2 * 60 * 60},
        {"id": 3, "name": "Thursday", "availability": 35 * 60},
        {"id": 4, "name": "Friday", "availability": 0 * 60 * 60},
        {"id": 5, "name": "Saturday", "availability": 2 * 60 * 60},
        {"id": 6, "name": "Sunday", "availability": 0 * 60 * 60},
    ]
    microcycle_weekdays =  [0, 1, 2, 3, 4, 5, 6]

    # Retrieve all possible phases.
    phases = (
        db.session.query(Phase_Library.id)
        .group_by(Phase_Library.id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    weekday_availability = []

    number_of_available_weekdays = 0
    total_availability = 0
    for day in microcycle_weekdays:
        availability = weekday_availability_temp[day]["availability"]
        weekday_availability.append({
            "id": weekday_availability_temp[day]["id"], 
            "name": weekday_availability_temp[day]["name"].title(), 
            "availability": availability
        })
        total_availability += availability
        if availability > 0:
            number_of_available_weekdays += 1

    for phase in phases:
        result = perform_workout_day_selection(phase.id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays)
        if verbose:
            print(str(phase.id))
            print(result["formatted"])
        test_results.append({
            # "phase_components": parameters["phase_components"], 
            "phase_id": phase.id,
            "result": result
        })
        if verbose:
            print("----------------------")

    return jsonify({"status": "success", "test_results": test_results}), 200