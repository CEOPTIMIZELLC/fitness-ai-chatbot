from config import verbose, verbose_formatted_schedule

from flask import abort
from flask_login import current_user

from app import db
from app.models import (
    User_Exercises, 
    User_Weekday_Availability, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Workout_Exercises
)

from app.agents.exercises import exercises_main

from app.utils.common_table_queries import current_workout_day
from app.utils.print_long_output import print_long_output

from app.main_agent.utils import retrieve_total_time_needed
from app.main_agent.utils import construct_user_workout_components_list, construct_available_exercises_list, construct_available_general_exercises_list
from app.main_agent.utils import verify_pc_information
from app.main_agent.utils import print_workout_exercises_schedule


# ----------------------------------------- Workout Exercises -----------------------------------------


def delete_old_children(workout_day_id):
    db.session.query(User_Workout_Exercises).filter_by(workout_day_id=workout_day_id).delete()
    if verbose:
        print("Successfully deleted")
    return None

def retrieve_availability_for_day(user_workout_day):
    # Retrieve availability for day.
    availability = (
        User_Weekday_Availability.query
        .filter_by(user_id=current_user.id, weekday_id=user_workout_day.weekday_id)
        .first())
    if availability:
        return int(availability.availability.total_seconds())
    return None

# Verifies and updates the phase component information.
# Updates the maximum allowed exercises to be the number of allowed exercises for a phase component if the number available is lower than the maximum.
def verify_and_update_pc_information(parameters, pcs, exercises):
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
def retrieve_pc_parameters(user_workout_day, availability):
    parameters = {"valid": True, "status": None}

    # Retrieve user components
    user_workout_components = user_workout_day.workout_components
    if not user_workout_components:
        abort(400, description="This phase component is inactive. No exercises for today.")

    parameters["one_rep_max_improvement_percentage"] = 25
    parameters["availability"] = availability
    parameters["phase_components"] = construct_user_workout_components_list(user_workout_components)
    parameters["possible_exercises"] = construct_available_exercises_list(current_user.id)
    parameters["possible_general_exercises"] = construct_available_general_exercises_list(parameters["possible_exercises"])

    verify_and_update_pc_information(parameters, parameters["phase_components"][1:], parameters["possible_exercises"][1:])

    parameters["projected_duration"] = retrieve_projected_duration(parameters["phase_components"][1:], parameters["phase_components"][1:])
    return parameters

def agent_output_to_sqlalchemy_model(exercises_output, workout_day_id):
    new_exercises = []
    for i, exercise in enumerate(exercises_output, start=1):
        # Create a new exercise entry.
        new_exercise = User_Workout_Exercises(
            workout_day_id = workout_day_id,
            phase_component_id = exercise["phase_component_id"],
            exercise_id = exercise["exercise_id"],
            bodypart_id = exercise["bodypart_id"],
            order = i,
            reps = exercise["reps_var"],
            sets = exercise["sets_var"],
            intensity = exercise["intensity_var"],
            rest = exercise["rest_var"],
            weight = exercise["training_weight"],
        )

        new_exercises.append(new_exercise)
    return new_exercises

class WorkoutActions:
    # Retrieve current user's workout exercises
    @staticmethod
    def get_user_list():
        user_workout_exercises = (
            User_Workout_Exercises.query
            .join(User_Workout_Days)
            .join(User_Microcycles)
            .join(User_Mesocycles)
            .join(User_Macrocycles)
            .filter_by(user_id=current_user.id)
            .all())
        return [user_workout_exercise.to_dict() 
                for user_workout_exercise in user_workout_exercises]

    # Retrieve user's current microcycle's workout exercises
    @staticmethod
    def get_user_current_list():
        user_workout_day = current_workout_day(current_user.id)
        if not user_workout_day:
            abort(404, description="No active workout day found.")

        user_workout_exercises = user_workout_day.exercises

        return [user_workout_exercise.to_dict() 
                for user_workout_exercise in user_workout_exercises]

    # Retrieve user's current microcycle's workout exercises
    @staticmethod
    def get_formatted_list():
        user_workout_day = current_workout_day(current_user.id)
        if not user_workout_day:
            abort(404, description="No active workout day found.")

        user_workout_exercises = user_workout_day.exercises
        if not user_workout_exercises:
            abort(404, description="No exercises for the day found.")
        
        loading_system_id = user_workout_day.loading_system_id

        user_workout_exercises_dict = [user_workout_exercise.to_dict() | 
                                    {"component_id": user_workout_exercise.phase_components.components.id}
                                    for user_workout_exercise in user_workout_exercises]
        
        formatted_schedule = print_workout_exercises_schedule(loading_system_id, user_workout_exercises_dict)
        if verbose_formatted_schedule:
            print_long_output(formatted_schedule)
        return formatted_schedule

    @staticmethod
    def scheduler():
        user_workout_day = current_workout_day(current_user.id)
        if not user_workout_day:
            abort(404, description="No active workout day found.")

        delete_old_children(user_workout_day.id)

        availability = retrieve_availability_for_day(user_workout_day)
        if not availability:
            abort(404, description="No active weekday availability found.")

        # Retrieve parameters.
        parameters = retrieve_pc_parameters(user_workout_day, availability)
        constraints={"vertical_loading": user_workout_day.loading_systems.id == 1}

        result = exercises_main(parameters, constraints)
        if verbose:
            print_long_output(result["formatted"])

        user_workout_exercises = agent_output_to_sqlalchemy_model(result["output"], user_workout_day.id)

        db.session.add_all(user_workout_exercises)
        db.session.commit()
        return result

    @staticmethod
    def complete_workout():
        result = []
        user_workout_day = current_workout_day(current_user.id)
        if not user_workout_day:
            abort(404, description="No active workout day found.")
        workout_exercises = user_workout_day.exercises

        for exercise in workout_exercises:
            user_exercise = db.session.get(User_Exercises, {"user_id": current_user.id, "exercise_id": exercise.exercise_id})

            new_weight = exercise.weight or 0

            new_one_rep_max = round((new_weight * (30 + exercise.reps)) / 30, 2)

            # Only replace if the new one rep max is larger.
            user_exercise.one_rep_max = max(user_exercise.one_rep_max_decayed, new_one_rep_max)
            user_exercise.one_rep_load = new_one_rep_max
            user_exercise.volume = exercise.volume
            user_exercise.density = exercise.density
            user_exercise.intensity = exercise.intensity
            user_exercise.duration = exercise.duration
            user_exercise.working_duration = exercise.working_duration
            user_exercise.last_performed = exercise.workout_days.date

            # Only replace if the new performance is larger.
            user_exercise.performance = max(user_exercise.performance_decayed, exercise.performance)

            db.session.commit()

            result.append(user_exercise.to_dict())

        return result
