from config import verbose_subagent_steps
from flask import current_app, abort
from datetime import timedelta

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.types import interrupt, Command

from .base_sub_agent import BaseAgent, TState, sub_agent_focused_items

# ----------------------------------------- Base Sub Agent With Availability -----------------------------------------

from app.main_agent.prompts import availability_system_prompt
from app.main_agent.impact_goal_models import AvailabilityGoal
from app.main_agent.user_weekdays_availability import create_availability_agent

class BaseAgentWithAvailability(BaseAgent):
    availability_focus = "availability"
    sub_agent_title = ""
    availability_title = "Availability"
    availability_system_prompt = availability_system_prompt
    availability_goal = AvailabilityGoal

    def availability_node(self, state: TState):
        print(f"\n=========Changing User Availability=========")
        if state["availability_impacted"]:
            availability_agent = create_availability_agent()
            result = availability_agent.invoke({
                "user_id": state["user_id"], 
                "user_input": state["user_input"], 
                "attempts": state["attempts"], 
                "availability_impacted": state["availability_impacted"], 
                "availability_message": state["availability_message"]
            })
        else:
            result = {
                "availability_impacted": False, 
                "availability_message": None, 
                "availability_formatted": None
            }
        return {
            "availability_impacted": result["availability_impacted"], 
            "availability_message": result["availability_message"], 
            "availability_formatted": result["availability_formatted"]
        }


    def __init__(self):
        super().__init__()
        self.availability_names = sub_agent_focused_items(self.availability_focus)

    def availability_retriever_agent(self, state):
        pass

    # Retrieve availability item that will be used for the current schedule.
    def retrieve_availability(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving {self.availability_title} for {self.sub_agent_title} Scheduling---------")
        return self.availability_retriever_agent(state)

    # Confirm that a currently active availability exists to attach the a schedule to.
    def confirm_availability(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Confirm there is an active {self.availability_title}---------")
        if not state[self.availability_names["entry"]]:
            return "no_availability"
        return "availability"


    # Request permission from user to execute the availability initialization.
    def ask_for_availability_permission(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Ask user if a new {self.availability_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.availability_title} exists. Would you like for me to generate a {self.availability_title} for you?"
        })
        user_input = result["user_input"]

        print(f"Extract the {self.availability_title} Goal the following message: {user_input}")
        human = f"Extract the goals from the following message: {user_input}"
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.availability_system_prompt),
                ("human", human),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(self.availability_goal)
        goal_classifier = check_prompt | structured_llm
        goal_class = goal_classifier.invoke({})

        return {
            self.availability_names["impact"]: goal_class.is_requested,
            self.availability_names["message"]: goal_class.detail
        }

    # Router for if permission was granted.
    def confirm_availability_permission(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Confirm the agent can create a new {self.availability_title}---------")
        if not state[self.availability_names["impact"]]:
            return "permission_denied"
        return "permission_granted"

    # State if the Availability isn't allowed to be requested.
    def availability_permission_denied(self, state: TState):
        if verbose_subagent_steps:
            print(f"\t---------Abort {self.sub_agent_title} Scheduling---------")
        abort(404, description=f"No active {self.availability_title} found.")
        return {}


