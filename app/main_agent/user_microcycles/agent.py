from logging_config import LogMainSubAgent
from datetime import timedelta

from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Microcycles, User_Mesocycles, User_Macrocycles
from app.utils.common_table_queries import current_mesocycle, current_microcycle

from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read, determine_read_operation, determine_read_filter_operation
from app.main_agent.base_sub_agents.with_parents import confirm_parent, confirm_permission
from app.impact_goal_models import MesocycleGoal
from app.goal_prompts import mesocycle_system_prompt
from app.main_agent.user_mesocycles import create_mesocycle_agent

from app.schedule_printers import MicrocycleSchedulePrinter

from app.agent_states.microcycles import AgentState

from app.altering_agents.microcycles.agent import create_main_agent_graph as create_altering_agent

# ----------------------------------------- User Microcycles -----------------------------------------

class SubAgent(BaseAgent):
    focus = "microcycle"
    parent = "mesocycle"
    sub_agent_title = "Microcycle"
    parent_title = "Mesocycle"
    parent_system_prompt = mesocycle_system_prompt
    parent_goal = MesocycleGoal
    parent_scheduler_agent = create_mesocycle_agent()
    schedule_printer_class = MicrocycleSchedulePrinter()
    altering_agent = create_altering_agent()

    # Retrieve the Microcycles belonging to the Mesocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.microcycles

    def user_list_query(self, user_id):
        return User_Microcycles.query.join(User_Mesocycles).join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_microcycle(user_id)

    def parent_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.phase_id = new_parent_id
        return parent_db_entry

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Microcycle Scheduling---------")
        user_mesocycle = state["user_mesocycle"]

        # Each microcycle must last 1 week.
        microcycle_duration = timedelta(weeks=1)

        # Find how many one week microcycles will be present in the mesocycle
        microcycle_count = user_mesocycle["duration_days"] // microcycle_duration.days
        microcycle_start = user_mesocycle["start_date"]

        return {
            "mesocycle_id": user_mesocycle["id"],
            "microcycle_duration": microcycle_duration,
            "microcycle_count": microcycle_count,
            "start_date": microcycle_start
        }

    # Query to delete all old microcycles belonging to the current mesocycle.
    def delete_children_query(self, parent_id):
        db.session.query(User_Microcycles).filter_by(mesocycle_id=parent_id).delete()
        db.session.commit()

    # Initializes the microcycle schedule for the current mesocycle.
    def perform_scheduler(self, state: AgentState):
        return {}

    # Initializes the microcycle schedule for the current mesocycle.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Perform Microcycle Scheduling---------")
        mesocycle_id = state["mesocycle_id"]
        microcycle_duration = state["microcycle_duration"]
        microcycle_count = state["microcycle_count"]
        microcycle_start = state["start_date"]

        # Create a microcycle for each week in the mesocycle.
        microcycles = []
        for i in range(microcycle_count):
            microcycle_end = microcycle_start + microcycle_duration
            new_microcycle = User_Microcycles(
                mesocycle_id = mesocycle_id,
                order = i+1,
                start_date = microcycle_start,
                end_date = microcycle_end,
            )

            microcycles.append(new_microcycle)

            # Shift the start of the next microcycle to be the end of the current.
            microcycle_start = microcycle_end

        db.session.add_all(microcycles)
        db.session.commit()

        return {}

    def create_main_agent_graph(self, state_class: type[AgentState]):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("retrieve_parent", self.retrieve_parent)
        workflow.add_node("ask_for_permission", self.ask_for_permission)
        workflow.add_node("parent_requests_extraction", self.parent_requests_extraction)
        workflow.add_node("permission_denied", self.permission_denied)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("parent_retrieved", self.parent_retrieved)
        workflow.add_node("operation_is_read", self.chained_conditional_inbetween)
        workflow.add_node("read_operation_is_plural", self.chained_conditional_inbetween)
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
        workflow.add_node("read_user_current_element", self.read_user_current_element)
        workflow.add_node("get_formatted_list", self.get_formatted_list)
        workflow.add_node("get_user_list", self.get_user_list)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "retrieve_parent"                             # Retrieve the parent element if an impact is indicated.
            }
        )

        # Whether a parent element exists.
        workflow.add_conditional_edges(
            "retrieve_parent",
            confirm_parent, 
            {
                "no_parent": "ask_for_permission",                      # No parent element exists.
                "parent": "parent_retrieved"                            # In between step for if a parent element exists.
            }
        )

        # Whether the goal is to alter user elements.
        workflow.add_conditional_edges(
            "parent_retrieved",
            determine_if_alter, 
            {
                "not_alter": "operation_is_not_alter",                  # In between step for if the operation is not alter.
                "alter": "altering_agent"                               # Start altering subagent.
            }
        )

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_alter",
            determine_if_read, 
            {
                "not_read": "end_node",                                 # End subagent if nothing is requested.
                "read": "operation_is_read"                             # In between step for if the operation is read.
            }
        )
        # Whether the read operations is for a single element or plural elements.
        workflow.add_conditional_edges(
            "operation_is_read",
            determine_read_operation, 
            {
                "plural": "read_operation_is_plural",                   # In between step for if the read operation is plural.
                "singular": "read_user_current_element"                 # Read the current element.
            }
        )

        # Whether the plural list is for all of the elements or all elements belonging to the user.
        workflow.add_conditional_edges(
            "read_operation_is_plural",
            determine_read_filter_operation, 
            {
                "current": "get_formatted_list",                        # Read the current schedule.
                "all": "get_user_list"                                  # Read all user elements.
            }
        )

        # Whether a parent element is allowed to be created where one doesn't already exist.
        workflow.add_edge("ask_for_permission", "parent_requests_extraction")
        workflow.add_conditional_edges(
            "parent_requests_extraction",
            confirm_permission, 
            {
                "permission_denied": "permission_denied",               # The agent isn't allowed to create a parent.
                "permission_granted": "parent_agent"                    # The agent is allowed to create a parent.
            }
        )
        workflow.add_edge("parent_agent", "retrieve_parent")

        workflow.add_edge("altering_agent", "end_node")
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("read_user_current_element", "end_node")
        workflow.add_edge("get_formatted_list", "end_node")
        workflow.add_edge("get_user_list", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)