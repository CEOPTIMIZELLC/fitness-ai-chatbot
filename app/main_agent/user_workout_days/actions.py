from config import vertical_loading
from config import verbose, verbose_formatted_schedule
from flask import abort
from flask_login import current_user
from datetime import timedelta

from app import db
from app.models import (
    Phase_Component_Library, 
    Bodypart_Library, 
    Weekday_Library, 
    User_Weekday_Availability, 
    User_Workout_Components, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days
)

from app.agents.phase_components import Main as phase_component_main

from app.utils.db_helpers import get_all_items
from app.utils.common_table_queries import current_microcycle, current_workout_day
from app.utils.print_long_output import print_long_output

from app.main_agent.utils import construct_available_exercises_list, construct_phase_component_list, construct_available_general_exercises_list
from app.main_agent.utils import verify_pc_information
from app.main_agent.utils import print_workout_days_schedule

# ----------------------------------------- Workout Days -----------------------------------------

def delete_old_children(microcycle_id):
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

        if vertical_loading:
            loading_system_id = 1
        else:
            loading_system_id = 2

        new_workday = User_Workout_Days(
            microcycle_id = microcycle_id,
            weekday_id = weekday_number,
            loading_system_id = loading_system_id,
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
    pc_info = verify_pc_information(parameters, pcs, exercises, total_availability, "duration_min_for_day", "frequency_per_microcycle_min", check_globally=False, default_count_if_none=number_of_available_weekdays)
    pcs = pc_info[0]
    parameters["phase_components"] = pcs
    return None

# Retrieves the parameters used by the solver.
def retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability):
    parameters = {"valid": True, "status": None}

    parameters["microcycle_weekdays"] = microcycle_weekdays
    parameters["weekday_availability"] = weekday_availability
    parameters["phase_components"] = construct_phase_component_list(phase_id)
    parameters["possible_exercises"] = construct_available_exercises_list(current_user.id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_pc_information(parameters, parameters["phase_components"], parameters["possible_exercises"][1:], total_availability, number_of_available_weekdays)

    return parameters

def perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose=False):
    parameters=retrieve_pc_parameters(phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability)
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

def retrieve_availability_for_week():
    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == current_user.id)
        .order_by(User_Weekday_Availability.user_id.asc())
        .all())
    return availability

def workout_day_executor(phase_id=None):
    user_microcycle = current_microcycle(current_user.id)
    if not user_microcycle:
        abort(404, description="No active microcycle found.")
    
    # If no phase id given, retrieve the currently active one. 
    if not phase_id:
        phase_id = user_microcycle.mesocycles.phase_id

    availability = retrieve_availability_for_week()
    if not availability:
        abort(404, description="No active weekday availability found.")

    delete_old_children(user_microcycle.id)
    microcycle_weekdays, user_workdays = duration_to_weekdays(user_microcycle.duration.days, user_microcycle.start_date, user_microcycle.id)

    weekday_availability, number_of_available_weekdays, total_availability = retrieve_weekday_availability_information_from_availability(availability)

    result = perform_workout_day_selection(phase_id, microcycle_weekdays, total_availability, weekday_availability, number_of_available_weekdays, verbose)

    if result["output"] == "error":
        abort(404, description=result["message"])

    user_workdays = agent_output_to_sqlalchemy_model(result["output"], user_workdays)
    db.session.add_all(user_workdays)
    db.session.commit()
    return result


class MicrocycleSchedulerActions:
    # Retrieve current user's phase components
    @staticmethod
    def get_user_list():
        user_workout_days = User_Workout_Days.query.join(User_Microcycles).join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=current_user.id).all()
        return [user_workout_day.to_dict() 
                for user_workout_day in user_workout_days]

    # Retrieve user's current microcycle's phase components
    @staticmethod
    def get_user_current_list():
        user_microcycle = current_microcycle(current_user.id)
        if not user_microcycle:
            abort(404, description="No active microcycle found.")
        user_workout_days = user_microcycle.workout_days
        return [user_workout_day.to_dict() 
                for user_workout_day in user_workout_days]

    # Retrieve user's current microcycle's phase components
    @staticmethod
    def get_formatted_list():
        user_microcycle = current_microcycle(current_user.id)
        if not user_microcycle:
            abort(404, description="No active microcycle found.")

        user_workout_days = user_microcycle.workout_days
        if not user_workout_days:
            abort(404, description="No workout days for the microcycle found.")

        user_workout_days_dict = [user_workout_day.to_dict() for user_workout_day in user_workout_days]

        pc_dict = get_all_items(Phase_Component_Library)
        bodypart_dict = get_all_items(Bodypart_Library)

        formatted_schedule = print_workout_days_schedule(pc_dict, bodypart_dict, user_workout_days_dict)
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return formatted_schedule

    # Retrieve user's current phase component
    @staticmethod
    def read_user_current_element():
        user_workout_day = current_workout_day(current_user.id)
        if not user_workout_day:
            abort(404, description="No active phase component found.")
        return user_workout_day.to_dict()

    # Assigns phase components to days along with projected length.
    @staticmethod
    def scheduler():
        # Retrieve results.
        result = workout_day_executor()
        return result

    # Assigns phase components to days along with projected length.
    @staticmethod
    def change_by_id(phase_id):
        # Retrieve results.
        result = workout_day_executor(phase_id)
        return result
