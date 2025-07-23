from config import vertical_loading, verbose, verbose_subagent_steps
from datetime import timedelta

from app.models import Weekday_Library, User_Weekday_Availability, User_Workout_Days

from app.main_agent.utils import construct_available_exercises_list, construct_phase_component_list, construct_available_general_exercises_list
from app.main_agent.utils import verify_pc_information

# ----------------------------------------- Workout Days -----------------------------------------

# Verifies and updates the phase component information.
# Updates the lower bound for duration if the user's current performance for all exercises in a phase component requires a higher minimum.
# Checks if the minimum amount of exercises allowed could fit into the workout with the current duration. 
# Checks if there are enough exercises to meet the minimum amount of exercises for a phase component. 
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_phase_component_information(parameters, pcs, exercises, total_availability, number_of_available_weekdays):
    pc_info = verify_pc_information(parameters, pcs, exercises, total_availability, "duration_min_for_day", "frequency_per_microcycle_min", check_globally=False, default_count_if_none=number_of_available_weekdays)
    pcs = pc_info[0]
    parameters["phase_components"] = pcs
    return None

# Retrieves the parameters used by the solver.
def retrieve_parameters(user_id, phase_id, microcycle_weekdays, weekday_availability, number_of_available_weekdays, total_availability):
    parameters = {"valid": True, "status": None}

    parameters["microcycle_weekdays"] = microcycle_weekdays
    parameters["weekday_availability"] = weekday_availability
    parameters["phase_components"] = construct_phase_component_list(phase_id)
    parameters["possible_exercises"] = construct_available_exercises_list(user_id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_phase_component_information(parameters, parameters["phase_components"], parameters["possible_exercises"][1:], total_availability, number_of_available_weekdays)

    return parameters

def retrieve_availability_for_week(user_id):
    availability = (
        User_Weekday_Availability.query
        .join(Weekday_Library)
        .filter(User_Weekday_Availability.user_id == user_id)
        .order_by(User_Weekday_Availability.user_id.asc())
        .all())
    return availability

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
            "id": day["weekday_id"], 
            "name": day["weekday_name"].title(), 
            "availability": int(day["availability"])
        })
        total_availability += day["availability"]
        if day["availability"] > 0:
            number_of_available_weekdays += 1
    return weekday_availability, number_of_available_weekdays, total_availability

# Given a start date and a duration, convert into a list of weekdays.
def duration_to_weekdays(dur, start_date):
    microcycle_weekdays = []
    start_date_number = start_date.weekday()

    # Loop through the number of iterations
    for i in range(dur):
        # Calculate the current number using modulo to handle the circular nature
        weekday_number = (start_date_number + i) % 7
        microcycle_weekdays.append(weekday_number)
    return microcycle_weekdays

# Create a corresponding workout day entry.
def workout_day_entry_construction(microcycle_weekdays, start_date, microcycle_id):
    user_workdays = []

    # Loop through the number of iterations
    for i, weekday_number in enumerate(microcycle_weekdays):
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
    
    return user_workdays
