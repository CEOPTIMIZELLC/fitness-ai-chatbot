from langgraph.graph import StateGraph, START, END

# Agent construction imports.
from app.main_sub_agents.base_sub_agents.with_parents import BaseAgentWithParents as BaseAgent
from app.main_sub_agents.base_sub_agents.base import confirm_impact, determine_if_create, determine_if_read
from app.agent_states.workout_schedule import AgentState

# Sub agent imports.
from app.creation_agents.workout_schedule import create_creation_agent
from app.reading_agents.workout_schedule import create_reading_agent
from app.parent_retriever_agents.workout_schedule import create_parent_retriever_agent
from app.parent_retriever_agents.workout_schedule import create_availability_retriever_agent

# ----------------------------------------- User Workout Exercises -----------------------------------------

class SubAgent(BaseAgent):
    focus = "workout_schedule"
    sub_agent_title = "Workout"
    parent_scheduler_agent = create_parent_retriever_agent()
    availability_scheduler_agent = create_availability_retriever_agent()
    creation_agent = create_creation_agent()
    reading_agent = create_reading_agent()

    # Create main agent.
    def create_main_agent_graph(self, state_class):
        workflow = StateGraph(state_class)
        workflow.add_node("start_node", self.start_node)
        workflow.add_node("parent_agent", self.parent_scheduler_agent)
        workflow.add_node("availability_agent", self.availability_scheduler_agent)
        workflow.add_node("extract_operations", self.extract_operations)
        workflow.add_node("creation_agent", self.creation_agent)
        workflow.add_node("operation_is_not_create", self.chained_conditional_inbetween)
        workflow.add_node("reading_agent", self.reading_agent)
        workflow.add_node("operation_is_not_read", self.chained_conditional_inbetween)
        workflow.add_node("end_node", self.end_node)

        # Whether the focus element has been indicated to be impacted.
        workflow.add_edge(START, "start_node")
        workflow.add_conditional_edges(
            "start_node",
            confirm_impact, 
            {
                "no_impact": "end_node",                                # End the sub agent if no impact is indicated.
                "impact": "parent_agent"                                # Retrieve the parent element if an impact is indicated.
            }
        )

        workflow.add_edge("parent_agent", "availability_agent")

        workflow.add_edge("availability_agent", "extract_operations")

        # Whether the goal is to create user elements.
        workflow.add_conditional_edges(
            "extract_operations",
            determine_if_create, 
            {
                "not_create": "operation_is_not_create",                # In between step for if the operation is not create.
                "create": "creation_agent"                              # Start createing subagent.
            }
        )
        workflow.add_edge("creation_agent", "operation_is_not_create")

        # Whether the goal is to read user elements.
        workflow.add_conditional_edges(
            "operation_is_not_create",
            determine_if_read, 
            {
                "not_read": "operation_is_not_read",                    # In between step for if the operation is not read.
                "read": "reading_agent"                                 # Start reading subagent.
            }
        )
        workflow.add_edge("reading_agent", "operation_is_not_read")

        workflow.add_edge("operation_is_not_read", "end_node")
        workflow.add_edge("end_node", END)

        return workflow.compile()

# Create main agent.
def create_main_agent_graph():
    agent = SubAgent()
    return agent.create_main_agent_graph(AgentState)