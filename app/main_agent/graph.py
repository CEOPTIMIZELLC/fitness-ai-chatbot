from logging_config import LogMainAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from flask import current_app
from flask_login import current_user

from .prompts import goal_extraction_system_prompt

from .user_macrocycles import MacrocycleAgentNode
from .user_mesocycles import create_mesocycle_agent
from .user_microcycles import create_microcycle_agent
from .user_workout_days import create_microcycle_scheduler_agent
from .user_workout_exercises import create_workout_agent
from .user_workout_completion import create_workout_completion_agent
from .user_weekdays_availability import WeekdayAvailabilityAgentNode

from .impact_goal_models import RoutineImpactGoals
from .main_agent_state import MainAgentState as AgentState


class MainAgent(WeekdayAvailabilityAgentNode, MacrocycleAgentNode):
    def entry_node(self, state: AgentState):
        LogMainAgent.agent_introductions(f"\n=========Beginning Main Agent=========")
        return {}

    # Confirm that the desired section should be impacted.
    def confirm_input(self, state):
        LogMainAgent.agent_introductions(f"\n=========Beginning Main Agent=========")
        LogMainAgent.agent_steps(f"\t---------Confirm that an Input Exists---------")
        if not state["user_input"]:
            LogMainAgent.agent_steps(f"\t---------No Input---------")
            return "no_input"
        return "included_input"

    def user_input_information_extraction(self, state: AgentState):
        LogMainAgent.agent_steps(f"\n=========Extract Input=========")
        user_input = state["user_input"]

        LogMainAgent.verbose(f"Extract the goals from the following message: {user_input}")
        human = f"Extract the goals from the following message: {user_input}"
        # human = f"New_goal: {user_input}"
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", goal_extraction_system_prompt),
                ("human", human),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(RoutineImpactGoals)
        goal_classifier = check_prompt | structured_llm
        goal_class = goal_classifier.invoke({})

        state["user_id"] = current_user.id
        state["attempts"] = 1
        state["availability_impacted"] = goal_class.availability.is_requested
        state["availability_is_altered"] = True
        state["availability_message"] = goal_class.availability.detail
        state["macrocycle_impacted"] = goal_class.macrocycle.is_requested
        state["macrocycle_is_altered"] = True
        state["macrocycle_message"] = goal_class.macrocycle.detail
        state["macrocycle_alter_old"] = goal_class.macrocycle.alter_old
        state["mesocycle_impacted"] = goal_class.mesocycle.is_requested
        state["mesocycle_is_altered"] = True
        state["mesocycle_message"] = goal_class.mesocycle.detail
        state["microcycle_impacted"] = goal_class.microcycle.is_requested
        state["microcycle_is_altered"] = True
        state["microcycle_message"] = goal_class.microcycle.detail
        state["phase_component_impacted"] = goal_class.phase_component.is_requested
        state["phase_component_is_altered"] = True
        state["phase_component_message"] = goal_class.phase_component.detail
        state["workout_schedule_impacted"] = goal_class.workout_schedule.is_requested
        state["workout_schedule_is_altered"] = True
        state["workout_schedule_message"] = goal_class.workout_schedule.detail
        state["workout_completion_impacted"] = goal_class.workout_completion.is_requested
        state["workout_completion_is_altered"] = True
        state["workout_completion_message"] = goal_class.workout_completion.detail

        LogMainAgent.input_info(f"Goals extracted.")
        if state["workout_completion_impacted"]:
            LogMainAgent.input_info(f"workout_completion: {state["workout_completion_message"]}")
        if state["availability_impacted"]:
            LogMainAgent.input_info(f"availability: {state["availability_message"]}")
        if state["macrocycle_impacted"]:
            LogMainAgent.input_info(f"macrocycle: {state["macrocycle_message"]}")
        if state["mesocycle_impacted"]:
            LogMainAgent.input_info(f"mesocycle: {state["mesocycle_message"]}")
        if state["microcycle_impacted"]:
            LogMainAgent.input_info(f"microcycle: {state["microcycle_message"]}")
        if state["phase_component_impacted"]:
            LogMainAgent.input_info(f"phase_component: {state["phase_component_message"]}")
        if state["workout_schedule_impacted"]:
            LogMainAgent.input_info(f"workout_schedule: {state["workout_schedule_message"]}")
        LogMainAgent.input_info("")

        return state

    def print_schedule_node(self, state: AgentState):
        LogMainAgent.agent_steps(f"\n=========Printing Schedule=========")
        LogMainAgent.formatted_schedule(f"Schedule Generatted.")
        if ("workout_completion_formatted" in state) and (state["workout_completion_impacted"]):
            LogMainAgent.formatted_schedule(f"workout_completion: \n{state["workout_completion_formatted"]}")
        if ("availability_formatted" in state) and (state["availability_impacted"]):
            LogMainAgent.formatted_schedule(f"availability: \n{state["availability_formatted"]}")
        if ("macrocycle_formatted" in state) and (state["macrocycle_impacted"]):
            LogMainAgent.formatted_schedule(f"macrocycle: \n{state["macrocycle_formatted"]}")
        if ("mesocycle_formatted" in state) and (state["mesocycle_impacted"]):
            LogMainAgent.formatted_schedule(f"mesocycle: \n{state["mesocycle_formatted"]}")
        if ("microcycle_formatted" in state) and (state["microcycle_impacted"]):
            LogMainAgent.formatted_schedule(f"microcycle: \n{state["microcycle_formatted"]}")
        if ("phase_component_formatted" in state) and (state["phase_component_impacted"]):
            LogMainAgent.formatted_schedule(f"phase_component: \n{state["phase_component_formatted"]}")
        if ("workout_schedule_formatted" in state) and (state["workout_schedule_impacted"]):
            LogMainAgent.formatted_schedule(f"workout_schedule: \n{state["workout_schedule_formatted"]}")
        LogMainAgent.formatted_schedule("")

        return state

    # Node to declare that the sub agent has ended.
    def end_node(self, state: AgentState):
        LogMainAgent.agent_introductions(f"=========Ending Main Agent=========\n")
        return {}

    # Create main agent.
    def create_main_agent_graph(self, checkpointer=None):
        mesocycle_agent = create_mesocycle_agent()
        microcycle_agent = create_microcycle_agent()
        microcycle_scheduler_agent = create_microcycle_scheduler_agent()
        workout_agent = create_workout_agent()
        workout_completion_agent = create_workout_completion_agent()

        workflow = StateGraph(AgentState)

        workflow.add_node("entry_node", self.entry_node)
        workflow.add_node("user_input_extraction", self.user_input_information_extraction)
        workflow.add_node("availability", self.availability_node)
        workflow.add_node("macrocycle", self.macrocycle_node)
        workflow.add_node("mesocycle", mesocycle_agent)
        workflow.add_node("microcycle", microcycle_agent)
        workflow.add_node("phase_component", microcycle_scheduler_agent)
        workflow.add_node("workout_schedule", workout_agent)
        workflow.add_node("workout_completion", workout_completion_agent)
        workflow.add_node("print_schedule", self.print_schedule_node)
        workflow.add_node("end_node", self.end_node)

        # Check whether a user input exists.
        workflow.add_conditional_edges(
            "entry_node",
            self.confirm_input,
            {
                "no_input": "end_node",                                     # End the agent if no input is given.
                "included_input": "user_input_extraction"                   # Parse the user input if one is given.
            }
        )

        # User Input to Workout Completion
        workflow.add_edge("user_input_extraction", "workout_completion")

        # Workout Completion to Availability and Macrocycles
        workflow.add_edge("workout_completion", "availability")
        workflow.add_edge("workout_completion", "macrocycle")

        # Availability and Macrocycles to Mesocycles
        workflow.add_edge("macrocycle", "mesocycle")
        workflow.add_edge("availability", "mesocycle")

        # Mesocycles to Microcycles
        workflow.add_edge("mesocycle", "microcycle")

        # Microcycles to Phase Components
        workflow.add_edge("microcycle", "phase_component")

        # Phase Components to Workout Exercises
        workflow.add_edge("phase_component", "workout_schedule")

        # Workout Exercises to End
        workflow.add_edge("workout_schedule", "print_schedule")
        workflow.add_edge("print_schedule", "end_node")

        workflow.set_entry_point("entry_node")
        workflow.set_finish_point("end_node")

        return workflow.compile(checkpointer=checkpointer)

# Create main agent.
def create_main_agent_graph(checkpointer):
    agent = MainAgent()
    return agent.create_main_agent_graph(checkpointer)