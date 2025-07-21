from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
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
    def user_input_information_extraction(self, state: AgentState):
        user_input = state["user_input"]

        print(f"Extract the goals from the following message: {user_input}")
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

        # # Reset to None for testing
        # if "workout_completion_formatted" in state:
        #     state["workout_completion_formatted"] = None
        # if "availability_formatted" in state:
        #     state["availability_formatted"] = None
        # if "macrocycle_formatted" in state:
        #     state["macrocycle_formatted"] = None
        # if "mesocycle_formatted" in state:
        #     state["mesocycle_formatted"] = None
        # if "microcycle_formatted" in state:
        #     state["microcycle_formatted"] = None
        # if "phase_component_formatted" in state:
        #     state["phase_component_formatted"] = None
        # if "workout_schedule_formatted" in state:
        #     state["workout_schedule_formatted"] = None

        print(f"Goals extracted.")
        if state["workout_completion_impacted"]:
            print(f"workout_completion: {state["workout_completion_message"]}")
        if state["availability_impacted"]:
            print(f"availability: {state["availability_message"]}")
        if state["macrocycle_impacted"]:
            print(f"macrocycle: {state["macrocycle_message"]}")
        if state["mesocycle_impacted"]:
            print(f"mesocycle: {state["mesocycle_message"]}")
        if state["microcycle_impacted"]:
            print(f"microcycle: {state["microcycle_message"]}")
        if state["phase_component_impacted"]:
            print(f"phase_component: {state["phase_component_message"]}")
        if state["workout_schedule_impacted"]:
            print(f"workout_schedule: {state["workout_schedule_message"]}")
        print("")

        return state

    def print_schedule_node(self, state: AgentState):
        print(f"\n=========Printing Schedule=========")
        print(f"Goals extracted.")
        if ("workout_completion_formatted" in state) and (state["workout_completion_impacted"]):
            print(f"workout_completion: \n{state["workout_completion_formatted"]}")
        if ("availability_formatted" in state) and (state["availability_impacted"]):
            print(f"availability: \n{state["availability_formatted"]}")
        if ("macrocycle_formatted" in state) and (state["macrocycle_impacted"]):
            print(f"macrocycle: \n{state["macrocycle_formatted"]}")
        if ("mesocycle_formatted" in state) and (state["mesocycle_impacted"]):
            print(f"mesocycle: \n{state["mesocycle_formatted"]}")
        if ("microcycle_formatted" in state) and (state["microcycle_impacted"]):
            print(f"microcycle: \n{state["microcycle_formatted"]}")
        if ("phase_component_formatted" in state) and (state["phase_component_impacted"]):
            print(f"phase_component: \n{state["phase_component_formatted"]}")
        if ("workout_schedule_formatted" in state) and (state["workout_schedule_impacted"]):
            print(f"workout_schedule: \n{state["workout_schedule_formatted"]}")
        print("")

        return state

    # Create main agent.
    def create_main_agent_graph(self, checkpointer=None):
        mesocycle_agent = create_mesocycle_agent()
        microcycle_agent = create_microcycle_agent()
        microcycle_scheduler_agent = create_microcycle_scheduler_agent()
        workout_agent = create_workout_agent()
        workout_completion_agent = create_workout_completion_agent()

        workflow = StateGraph(AgentState)

        workflow.add_node("user_input_extraction", self.user_input_information_extraction)

        workflow.add_node("availability", self.availability_node)
        workflow.add_node("macrocycle", self.macrocycle_node)
        workflow.add_node("mesocycle", mesocycle_agent)
        workflow.add_node("microcycle", microcycle_agent)
        workflow.add_node("phase_component", microcycle_scheduler_agent)
        workflow.add_node("workout_schedule", workout_agent)
        workflow.add_node("workout_completion", workout_completion_agent)
        workflow.add_node("print_schedule", self.print_schedule_node)

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
        workflow.add_edge("print_schedule", END)

        workflow.set_entry_point("user_input_extraction")

        return workflow.compile(checkpointer=checkpointer)

# Create main agent.
def create_main_agent_graph(checkpointer):
    agent = MainAgent()
    return agent.create_main_agent_graph(checkpointer)