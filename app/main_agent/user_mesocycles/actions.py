from config import verbose, verbose_formatted_schedule
from flask import abort
from flask_login import current_user
from datetime import timedelta

from app import db
from app.models import User_Mesocycles, User_Macrocycles

from app.agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

from app.main_agent.utils import construct_phases_list
from .schedule_printer import Main as print_schedule

# ----------------------------------------- User Mesocycles -----------------------------------------

def delete_old_children(macrocycle_id):
    db.session.query(User_Mesocycles).filter_by(macrocycle_id=macrocycle_id).delete()
    if verbose:
        print("Successfully deleted")

def perform_phase_selection(goal_id, macrocycle_allowed_weeks):
    parameters={
        "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
        "goal_type": goal_id}
    constraints={}

    # Retrieve all possible phases that can be selected and convert them into a list form.
    parameters["possible_phases"] = construct_phases_list(int(goal_id))

    result = phase_main(parameters, constraints)

    if verbose:
        print(result["formatted"])
    return result

def agent_output_to_sqlalchemy_model(phases_output, macrocycle_id, mesocycle_start_date):
    # Convert output to form that may be stored.
    user_phases = []
    order = 1
    for phase in phases_output:
        new_phase = User_Mesocycles(
            macrocycle_id = macrocycle_id,
            phase_id = phase["id"],
            is_goal_phase = phase["is_goal_phase"],
            order = order,
            start_date = mesocycle_start_date,
            end_date = mesocycle_start_date + timedelta(weeks=phase["duration"])
        )
        user_phases.append(new_phase)

        # Set startdate of next phase to be at the end of the current one.
        mesocycle_start_date +=timedelta(weeks=phase["duration"])
        order += 1
    return user_phases

def scheduler_main(goal_id=None):
    user_macro = current_macrocycle(current_user.id)
    if not user_macro:
        abort(404, description="No active macrocycle found.")
    
    if not goal_id:
        goal_id = user_macro.goal_id

    delete_old_children(user_macro.id)
    result = perform_phase_selection(goal_id, 26)
    user_phases = agent_output_to_sqlalchemy_model(result["output"], user_macro.id, user_macro.start_date)
    db.session.add_all(user_phases)
    db.session.commit()
    return result