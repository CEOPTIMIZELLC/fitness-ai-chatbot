from config import verbose, verbose_subagent_steps
from flask import current_app
from datetime import timedelta

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.types import interrupt

from app import db
from app.models import User_Mesocycles, User_Macrocycles
from app.agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

from app.main_agent.user_macrocycles import create_goal_agent
from app.main_agent.main_agent_state import MainAgentState
from app.main_agent.base_sub_agent import BaseAgent
from app.main_agent.impact_goal_models import MacrocycleGoal
from app.main_agent.prompts import macrocycle_system_prompt
from app.main_agent.utils import construct_phases_list

from .schedule_printer import MesocycleSchedulePrinter

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class AgentState(MainAgentState):
    user_macrocycle: dict
    macrocycle_id: int
    goal_id: int
    start_date: any
    macrocycle_allowed_weeks: int
    possible_phases: list
    agent_output: list

class SubAgent(BaseAgent):
    def parent_scheduler_agent(self, state: AgentState):
        print(f"\n---------Changing User Macrocycle---------")
        if state["macrocycle_impacted"]:
            goal_agent = create_goal_agent()
            result = goal_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "macrocycle_impacted": state["macrocycle_impacted"], 
                "macrocycle_message": state["macrocycle_message"],
                "macrocycle_alter_old": state["macrocycle_alter_old"]
            })
        else:
            result = {
                "macrocycle_message": None, 
                "macrocycle_formatted": None, 
                "macrocycle_alter_old": False
            }
        return {
            "macrocycle_impacted": result["macrocycle_impacted"], 
            "macrocycle_message": result["macrocycle_message"], 
            "macrocycle_formatted": result["macrocycle_formatted"], 
            "macrocycle_alter_old": result["macrocycle_alter_old"]
        }

    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    parent_title = "Macrocycle"
    parent_system_prompt = macrocycle_system_prompt
    parent_goal = MacrocycleGoal
    schedule_printer_class = MesocycleSchedulePrinter

    # Retrieve the Mesocycles belonging to the Macrocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.mesocycles

    def user_list_query(user_id):
        return User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Request permission from user to execute the parent initialization.
    def ask_for_parent_permission(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Ask user if a new Macrocycle can be made---------")
        result = interrupt({
            "task": "No current Macrocycle exists. Would you like for me to generate a macrocycle for you?"
        })
        user_input = result["user_input"]

        print(f"Extract the Macrocycle Goal the following message: {user_input}")
        human = f"Extract the goals from the following message: {user_input}"
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", macrocycle_system_prompt),
                ("human", human),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(MacrocycleGoal)
        goal_classifier = check_prompt | structured_llm
        goal_class = goal_classifier.invoke({})

        return {
            "macrocycle_impacted": goal_class.is_requested,
            "macrocycle_message": goal_class.detail, 
            "macrocycle_alter_old": goal_class.alter_old
        }

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Information for Mesocycle Scheduling---------")
        user_macrocycle = state["user_macrocycle"]
        macrocycle_id = user_macrocycle["id"]
        goal_id = user_macrocycle["goal_id"]
        start_date = user_macrocycle["start_date"]
        macrocycle_allowed_weeks = macrocycle_weeks
        possible_phases = construct_phases_list(int(goal_id))
        return {
            "macrocycle_id": macrocycle_id,
            "goal_id": goal_id,
            "start_date": start_date,
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "possible_phases": possible_phases
        }

    # Query to delete all old mesocycles belonging to the current macrocycle.
    def delete_children_query(self, parent_id):
        db.session.query(User_Mesocycles).filter_by(macrocycle_id=parent_id).delete()
        db.session.commit()

    # Executes the agent to create the mesocycle/phase schedule for the current macrocycle.
    def perform_scheduler(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Perform Mesocycle Scheduling---------")
        goal_id = state["goal_id"]
        macrocycle_allowed_weeks = state["macrocycle_allowed_weeks"]
        parameters={
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "goal_type": goal_id}
        constraints={}

        # Retrieve all possible phases that can be selected and convert them into a list form.
        parameters["possible_phases"] = construct_phases_list(int(goal_id))

        result = phase_main(parameters, constraints)

        if verbose:
            print(result["formatted"])
        return {
            "agent_output": result["output"]
        }

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        if verbose_subagent_steps:
            print(f"\t---------Convert schedule to SQLAlchemy models.---------")
        phases_output = state["agent_output"]
        macrocycle_id = state["macrocycle_id"]
        mesocycle_start_date = state["start_date"]

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

        db.session.add_all(user_phases)
        db.session.commit()
        return {}

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)