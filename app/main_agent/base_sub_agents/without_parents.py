from config import verbose_formatted_schedule, verbose_subagent_steps
from flask import current_app, abort

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.types import interrupt

from .base import BaseAgent
from .utils import sub_agent_focused_items

# ----------------------------------------- Base Sub Agent For Schedule Items Without Parents -----------------------------------------

class BaseAgentWithoutParents(BaseAgent):
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    def user_list_query(self, user_id):
        pass

    def focus_retriever_agent(self, user_id):
        pass

    def focus_list_retriever_agent(self, user_id):
        pass

    # Check if a new goal exists to be classified.
    def confirm_if_performing_by_id(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Confirm that the {self.sub_agent_title} input is meant to just use an ID.---------")
        perform_with_parent_id_key = self.focus_names["perform_with_parent_id"]
        if perform_with_parent_id_key in state and state[perform_with_parent_id_key]:
            return "present_direct_goal_id"
        return "no_direct_goal_id"

    # Check if a new goal exists to be classified.
    def confirm_new_input(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Confirm there is a new {self.sub_agent_title} input to be parsed---------")
        if not state[self.focus_names["message"]]:
            return "no_new_input"
        return "present_new_input"

    # Request permission from user to execute the new input.
    def ask_for_new_input(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Ask user if a new {self.sub_agent_title} can be made---------")
        result = interrupt({
            "task": f"No current {self.sub_agent_title} exists. Would you like for me to generate a {self.sub_agent_title} for you?"
        })
        user_input = result["user_input"]

        print(f"Extract the {self.sub_agent_title} Goal the following message: {user_input}")
        human = f"Extract the goals from the following message: {user_input}"
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.focus_system_prompt),
                ("human", human),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(self.focus_goal)
        goal_classifier = check_prompt | structured_llm
        goal_class = goal_classifier.invoke({})

        return self.goal_classifier_parser(self.focus_names, goal_class)

    # State if no new input was requested.
    def no_new_input_requested(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Abort {self.sub_agent_title} Parsing---------")
        abort(404, description=f"No active {self.sub_agent_title} requested.")
        return {}

    def perform_input_parser(self, state):
        pass

    # Delete the old children belonging to the current item.
    def delete_old_children(self, state):
        pass

    # Convert output from the agent to SQL models.
    def agent_output_to_sqlalchemy_model(self, state):
        pass

    # Print output.
    def get_formatted_list(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Formatted {self.sub_agent_title} Schedule---------")
        user_id = state["user_id"]
        schedule_from_db = self.focus_list_retriever_agent(user_id)

        schedule_dict = [schedule_entry.to_dict() for schedule_entry in schedule_from_db]

        formatted_schedule = self.run_schedule_printer(schedule_dict)
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}
