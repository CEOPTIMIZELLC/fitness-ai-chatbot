from config import verbose, verbose_formatted_schedule, verbose_agent_introductions, verbose_subagent_steps
from flask import current_app, abort

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.types import interrupt, Command


# ----------------------------------------- Base Sub Agent -----------------------------------------

def sub_agent_focused_items(sub_agent_focus):
    return {
        "entry": f"user_{sub_agent_focus}", 
        "id": f"{sub_agent_focus}_id", 
        "impact": f"{sub_agent_focus}_impacted", 
        "message": f"{sub_agent_focus}_message", 
        "formatted": f"{sub_agent_focus}_formatted"
    }

class BaseAgent():
    focus = ""
    sub_agent_title = ""
    focus_system_prompt = None
    focus_goal = None

    def __init__(self):
        self.focus_names = sub_agent_focused_items(self.focus)

    def user_list_query(user_id):
        pass

    def focus_retriever_agent(self, user_id):
        pass

    # Confirm that the desired section should be impacted.
    def confirm_impact(self, state):
        if verbose_agent_introductions:
            print(f"\n=========Beginning User {self.sub_agent_title} Sub Agent=========")
        if verbose_subagent_steps:
            print(f"\t---------Confirm that the {self.sub_agent_title} is Impacted---------")
        if not state[self.focus_names["impact"]]:
            if verbose_subagent_steps:
                print(f"\t---------No Impact---------")
            return "no_impact"
        return "impact"

    # In between node for chained conditional edges.
    def impact_confirmed(self, state):
        return {}

    # Check if a new goal exists to be classified.
    def confirm_new_input(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Confirm there is a new {self.sub_agent_title} input to be parsed---------")
        if not state[self.focus_names["message"]]:
            return "no_new_input"
        return "present_new_input"

    # Default items extracted from the goal classifier
    def goal_classifier_parser(self, focus_names, goal_class):
        return {
            focus_names["impact"]: goal_class.is_requested,
            focus_names["message"]: goal_class.detail
        }

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
        formatted_schedule = state[self.focus_names["message"]]
        if verbose_formatted_schedule:
            print(formatted_schedule)
        return {self.focus_names["formatted"]: formatted_schedule}

    # Node to declare that the sub agent has ended.
    def end_node(self, state):
        if verbose_agent_introductions:
            print(f"=========Ending User {self.sub_agent_title} SubAgent=========\n")
        return {}

    # Retrieve all items for current user
    def get_user_list(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving All {self.sub_agent_title} for User---------")
        user_id = state["user_id"]
        user_list_from_db = self.user_list_query(user_id)

        return [user_list_entry.to_dict() for user_list_entry in user_list_from_db]

    # Retrieve user's current schedule item.
    def read_user_current_element(self, state):
        if verbose_subagent_steps:
            print(f"\t---------Retrieving Current {self.sub_agent_title} for User---------")
        user_id = state["user_id"]
        entry_from_db = self.focus_retriever_agent(user_id)
        if not entry_from_db:
            abort(404, description=f"No active {self.sub_agent_title} found.")
        return entry_from_db.to_dict()



