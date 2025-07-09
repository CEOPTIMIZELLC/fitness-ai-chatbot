from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import abort
from langgraph.graph import StateGraph, START, END


from app import db
from app.models import User_Weekday_Availability, User_Workout_Days

from app.utils.common_table_queries import current_microcycle

from .actions import retrieve_weekday_types
from typing_extensions import TypedDict

from app.agents.weekday_availability import create_weekday_availability_extraction_graph

# ----------------------------------------- User Availability -----------------------------------------

class AgentState(TypedDict):
    user_id: int

    user_input: str
    attempts: int

    availability_impacted: bool
    availability_message: str
    availability_formatted: str

    agent_output: list
    sql_models: any

# Confirm that the desired section should be impacted.
def confirm_impact(state: AgentState):
    if verbose_agent_introductions:
        print(f"\n=========Changing User Weekday Availability=========")
    if verbose_subagent_steps:
        print(f"---------Confirm that the User Weekday Availability is Impacted---------")
    if not state["availability_impacted"]:
        if verbose_subagent_steps:
            print(f"---------No Impact---------")
        return "no_impact"
    return "impact"

# In between node for chained conditional edges.
def impact_confirmed(state: AgentState):
    return {}

# Check if a new goal exists to be classified.
def confirm_new_availability(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Confirm there is an availability input to be parsed---------")
    if not state["availability_message"]:
        return "no_availability_input"
    return "present_availability_input"

# Ask user for a new goal if one isn't in the initial request.
def ask_for_new_availability(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Ask user for a new availability---------")
    return {
        "availability_impacted": True,
        "availability_message": "I should have 30 minutes every day now."
    }

# State if the goal isn't requested.
def no_availability_requested(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Abort Availability Parser---------")
    abort(404, description="No availability requested.")
    return {}

# Classify the new goal in one of the possible goal types.
def perform_availability_parsing(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Perform Availability Parsing---------")
    new_availability = state["availability_message"]

    # There are only so many types a weekday can be classified as, with all of them being stored.
    weekday_types = retrieve_weekday_types()
    weekday_app = create_weekday_availability_extraction_graph()

    # Invoke with new weekday and possible weekday types.
    result = weekday_app.invoke(
        {
            "new_availability": new_availability, 
            "weekday_types": weekday_types, 
            "attempts": 0
        })
    
    return {"agent_output": result["weekday_availability"]}

# Convert output from the agent to SQL models.
def agent_output_to_sqlalchemy_model(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Convert schedule to SQLAlchemy models.---------")
    user_id = state["user_id"]
    weekday_availability = state["agent_output"]
    # Update each availability entry to the database.
    for i in weekday_availability:
        db_entry = User_Weekday_Availability(user_id=user_id, 
                                            weekday_id=i["weekday_id"], 
                                            availability=i["availability"])
        db.session.merge(db_entry)
    db.session.commit()
    return {}

# Delete the old items belonging to the parent.
def delete_old_children(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Delete old items of current Weekday Availability---------")
    user_id = state["user_id"]
    user_microcycle = current_microcycle(user_id)
    if user_microcycle:
        microcycle_id = user_microcycle.id

        db.session.query(User_Workout_Days).filter_by(microcycle_id=microcycle_id).delete()
        if verbose:
            print("Successfully deleted")
    return {}

# Print output.
def get_formatted_list(state: AgentState):
    if verbose_subagent_steps:
        print(f"---------Retrieving Formatted Schedule for user---------")
    availability_message = state["availability_message"]
    if verbose_formatted_schedule:
        print(availability_message)
    return {"availability_formatted": availability_message}

# Node to declare that the sub agent has ended.
def end_node(state: AgentState):
    if verbose_agent_introductions:
        print(f"=========Ending User Availability=========\n")
    return {}

# Create main agent.
def create_main_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("impact_confirmed", impact_confirmed)
    workflow.add_node("ask_for_new_availability", ask_for_new_availability)
    workflow.add_node("perform_availability_parsing", perform_availability_parsing)
    workflow.add_node("delete_old_children", delete_old_children)
    workflow.add_node("agent_output_to_sqlalchemy_model", agent_output_to_sqlalchemy_model)
    workflow.add_node("get_formatted_list", get_formatted_list)
    workflow.add_node("no_availability_requested", no_availability_requested)
    workflow.add_node("end_node", end_node)

    workflow.add_conditional_edges(
        START,
        confirm_impact,
        {
            "no_impact": "end_node",
            "impact": "impact_confirmed"
        }
    )

    workflow.add_conditional_edges(
        "impact_confirmed",
        confirm_new_availability,
        {
            "no_availability_input": "ask_for_new_availability",
            "present_availability_input": "delete_old_children"
        }
    )

    workflow.add_conditional_edges(
        "ask_for_new_availability",
        confirm_new_availability,
        {
            "no_availability_input": "no_availability_requested",
            "present_availability_input": "delete_old_children"
        }
    )

    workflow.add_edge("delete_old_children", "perform_availability_parsing")
    workflow.add_edge("perform_availability_parsing", "agent_output_to_sqlalchemy_model")
    workflow.add_edge("agent_output_to_sqlalchemy_model", "get_formatted_list")
    workflow.add_edge("no_availability_requested", "end_node")
    workflow.add_edge("get_formatted_list", "end_node")
    workflow.add_edge("end_node", END)

    return workflow.compile()
