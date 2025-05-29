from config import verbose
from flask import jsonify, Blueprint
from flask_login import current_user, login_required
import math
from datetime import timedelta

from app import db
from app.models import (
    Phase_Library, 
    Phase_Component_Library, 
    Phase_Component_Bodyparts, 
    Weekday_Library, 
    User_Weekday_Availability, 
    User_Workout_Components, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.agents.phase_components import Main as phase_component_main

from app.utils.common_table_queries import current_microcycle, current_workout_day, user_possible_exercises_with_user_exercise_info
from app.utils.print_long_output import print_long_output

from app.routes.utils import construct_available_exercises_list, construct_phase_component_list

from app.routes.utils import verify_pc_information

bp = Blueprint('user_workout_days', __name__)

# ----------------------------------------- Workout Days -----------------------------------------

def delete_old_user_workout_days(microcycle_id):
    db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
    if verbose:
        print("Successfully deleted")

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

# Retrieves various availability information from the availability query.
# The availability for each weekday, as well as its name.
# The total number of available weekdays.
# The total availability over all. 
def retrieve_weekday_availability_information_from_availability(availability):
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
    return weekday_availability, number_of_available_weekdays, total_availability

# Verifies and updates the phase component information.
# Updates the lower bound for duration if the user's current performance for all exercises in a phase component requires a higher minimum.
# Checks if the minimum amount of exercises allowed could fit into the workout with the current duration. 
# Checks if there are enough exercises to meet the minimum amount of exercises for a phase component. 
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_pc_information(parameters, pcs, exercises, total_availability, number_of_available_weekdays):
    # Retrieve parameters. If a tuple is returned, that means they are the phase components, exercises, and exercises for phase components.
    verification_message = verify_pc_information(parameters, pcs, exercises, total_availability, "duration_min_for_day", "frequency_per_microcycle_min", check_globally=False, default_count_if_none=number_of_available_weekdays)
    if isinstance(verification_message, tuple):
        pcs = verification_message[0]
    else:
        return verification_message    # Replace the list of phase components with the corrected version. 

    parameters["phase_components"] = pcs
    return None

# Retrieves the parameters used by the solver.
def retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability):
    parameters = {"valid": True, "status": None}

    possible_pc_list = construct_phase_component_list(phase_id)
    for pc in possible_pc_list:
        pc["duration_min_for_day"] = (pc["duration_min"]) * (pc["exercises_per_bodypart_workout_min"] or 1)
        pc["duration_max_for_day"] = (pc["duration_max"]) * (pc["exercises_per_bodypart_workout_max"] or 1)

    parameters["microcycle_weekdays"] = microcycle_weekdays
    parameters["weekday_availability"] = weekday_availability
    parameters["phase_components"] = possible_pc_list
    exercises_with_component_phases = user_possible_exercises_with_user_exercise_info(current_user.id)
    parameters["possible_exercises"] = construct_available_exercises_list(exercises_with_component_phases)

    pc_verification_message = verify_and_update_pc_information(parameters, parameters["phase_components"], parameters["possible_exercises"][1:], total_availability, number_of_available_weekdays)
    if pc_verification_message:
        return jsonify({"status": "error", "message": pc_verification_message}), 400

    return parameters

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters=retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)

    # If a tuple error message is returned, return 
    if isinstance(parameters, tuple):
        return parameters
    constraints={}

    result = phase_component_main(parameters, constraints)
    if verbose:
        print_long_output(result["formatted"])
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


def workout_day_executor(phase_id=None):
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        return jsonify({"status": "error", "message": "No active microcycle found."}), 404
    
    # If no phase id given, retrieve the currently active one. 
    if not phase_id:
        phase_id = user_microcycle.mesocycles.phase_id

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

    weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(availability)

    result = perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)
    # If a tuple error message is returned, return 
    if isinstance(result, tuple):
        return result

    if result["output"] == "error":
        return jsonify({"status": "error", "message": result["message"]}), 404

    user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)
    db.session.add_all(user_workdays)
    db.session.commit()

    return result


# Assigns phase components to days along with projected length.
@bp.route('/', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer():
    # Retrieve results. If a tuple error message is returned, return the error message.
    result = workout_day_executor()
    if isinstance(result, tuple):
        return result
    return jsonify({"status": "success", "workdays": result}), 200

# Assigns phase components to days along with projected length.
@bp.route('/<phase_id>', methods=['POST', 'PATCH'])
@login_required
def workout_day_initializer_by_id(phase_id):
    # Retrieve results. If a tuple error message is returned, return the error message.
    result = workout_day_executor(phase_id)
    if isinstance(result, tuple):
        return result
    return jsonify({"status": "success", "workdays": result}), 200


def retrieve_availability_for_test():
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
    return microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability

# Testing for the parameter programming for phase component assignment.
@bp.route('/test/<phase_id>', methods=['GET', 'POST'])
def test_workout_day_by_id(phase_id):
    microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability = retrieve_availability_for_test()
    result = perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)

    # If a tuple error message is returned, return 
    if isinstance(result, tuple):
        return result

    return jsonify({"status": "success", "mesocycles": result}), 200

# Testing for the parameter programming for phase component assignment.
@bp.route('/test', methods=['GET', 'POST'])
def phase_component_classification_test():
    test_results = []

    # Retrieve all possible phases.
    phases = (
        db.session.query(Phase_Library.id)
        .group_by(Phase_Library.id)
        .order_by(Phase_Library.id.asc())
        .all()
    )

    microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability = retrieve_availability_for_test()

    for phase in phases:
        result = perform_workout_day_selection(phase.id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays)
        # If a tuple error message is returned, return 
        if isinstance(result, tuple):
            return result

        if verbose:
            print(str(phase.id))
            print_long_output(result["formatted"])
        test_results.append({
            # "phase_components": parameters["phase_components"], 
            "phase_id": phase.id,
            "result": result
        })
        if verbose:
            print("----------------------")

    return jsonify({"status": "success", "test_results": test_results}), 200