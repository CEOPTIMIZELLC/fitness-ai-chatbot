from logging_config import LogMainSubAgent
from datetime import timedelta

from langgraph.graph import StateGraph, START, END

from app import db
from app.models import User_Mesocycles, User_Macrocycles
from app.solver_agents.phases import Main as phase_main
from app.utils.common_table_queries import current_macrocycle, current_mesocycle

from app.main_agent.user_macrocycles import MacrocycleAgentNode
from app.main_agent.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_agent.base_sub_agents.base import confirm_impact, determine_if_alter, determine_if_read, determine_read_operation, determine_read_filter_operation, confirm_regenerate
from app.main_agent.base_sub_agents.with_parents import confirm_parent, confirm_permission
from app.impact_goal_models import MacrocycleGoal
from app.goal_prompts import macrocycle_system_prompt
from app.edit_agents import create_mesocycle_edit_agent
from app.main_agent.utils import construct_phases_list

from app.schedule_printers import MesocycleSchedulePrinter
from app.agent_states.mesocycles import AgentState

from app.altering_agents.mesocycles.agent import create_main_agent_graph as create_altering_agent
from app.reading_agents.mesocycles.agent import create_main_agent_graph as create_reading_agent

# ----------------------------------------- User Mesocycles -----------------------------------------

macrocycle_weeks = 26

class SubAgent(MacrocycleAgentNode, BaseAgent):
    focus = "mesocycle"
    parent = "macrocycle"
    sub_agent_title = "Mesocycle"
    parent_title = "Macrocycle"
    parent_system_prompt = macrocycle_system_prompt
    parent_goal = MacrocycleGoal
    parent_scheduler_agent = MacrocycleAgentNode.macrocycle_node
    focus_edit_agent = create_mesocycle_edit_agent()
    schedule_printer_class = MesocycleSchedulePrinter()
    altering_agent = create_altering_agent()
    reading_agent = create_reading_agent()

    # Retrieve the Mesocycles belonging to the Macrocycle.
    def retrieve_children_entries_from_parent(self, parent_db_entry):
        return parent_db_entry.mesocycles

    def user_list_query(self, user_id):
        return User_Mesocycles.query.join(User_Macrocycles).filter_by(user_id=user_id).all()

    def focus_retriever_agent(self, user_id):
        return current_mesocycle(user_id)

    def parent_retriever_agent(self, user_id):
        return current_macrocycle(user_id)

    # Changes the id of the parent.
    def parent_changer(self, user_id, new_parent_id):
        parent_db_entry = self.parent_retriever_agent(user_id)
        parent_db_entry.goal_id = new_parent_id
        return parent_db_entry

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        goal_class_dump = goal_class.model_dump()
        parsed_goal = {
            focus_names["is_altered"]: True,
            focus_names["read_plural"]: False,
            focus_names["read_current"]: False,
            "macrocycle_alter_old": goal_class_dump.pop("alter_old", False), 
            "other_requests": goal_class_dump.pop("other_requests", None)
        }

        # Alter the variables in the state to match those retrieved from the LLM.
        for key, value in goal_class_dump.items():
            if value is not None:
                parsed_goal[focus_names[key]] = value

        return parsed_goal

    # Request is unique for Macrocycle for Mesocycle
    def parent_requests_extraction(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\n---------Extract Other Requests---------")
        return self.other_requests_information_extractor(state, self.parent, f"{self.parent}_other_requests")

    # Retrieve necessary information for the schedule creation.
    def retrieve_information(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Retrieving Information for Mesocycle Scheduling---------")
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
        LogMainSubAgent.agent_steps(f"\t---------Perform Mesocycle Scheduling---------")
        goal_id = state["goal_id"]
        macrocycle_allowed_weeks = state["macrocycle_allowed_weeks"]
        parameters={
            "macrocycle_allowed_weeks": macrocycle_allowed_weeks,
            "goal_type": goal_id}
        constraints={}

        # Retrieve all possible phases that can be selected and convert them into a list form.
        parameters["possible_phases"] = construct_phases_list(int(goal_id))

        result = phase_main(parameters, constraints)
        LogMainSubAgent.agent_output(result["formatted"])

        agent_output = result["output"]
        mesocycle_start_date = state["start_date"]

        # Add the startdates and enddates to the schedule items.
        for i, schedule_item in enumerate(agent_output, start=1):
            phase_duration = schedule_item["duration"]
            schedule_item["start_date"] = mesocycle_start_date
            schedule_item["end_date"] = mesocycle_start_date + timedelta(weeks=phase_duration)
            schedule_item["order"] = i

            # Set startdate of next phase to be at the end of the current one.
            mesocycle_start_date +=timedelta(weeks=phase_duration)

        return {
            "agent_output": agent_output,
            "schedule_printed": result["formatted"]
        }

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state: AgentState):
        LogMainSubAgent.agent_steps(f"\t---------Convert schedule to SQLAlchemy models.---------")
        phases_output = state["agent_output"]
        macrocycle_id = state["macrocycle_id"]

        # Convert output to form that may be stored.
        user_phases = []
        for phase in phases_output:
            new_phase = User_Mesocycles(
                macrocycle_id = macrocycle_id,
                phase_id = phase["id"],
                is_goal_phase = phase["is_goal_phase"],
                order = phase["order"],
                start_date = phase["start_date"],
                end_date = phase["end_date"]
            )

            user_phases.append(new_phase)

        db.session.add_all(user_phases)
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
        workflow.add_node("altering_agent", self.altering_agent)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("operation_is_not_alter", self.chained_conditional_inbetween)
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
                "read": "reading_agent"                                 # Start reading subagent.
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
        workflow.add_edge("reading_agent", "end_node")
        workflow.add_edge("permission_denied", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)