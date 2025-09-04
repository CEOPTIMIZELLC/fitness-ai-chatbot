from logging_config import LogEditorAgent

from pydantic import BaseModel, Field

from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Request permission from user to execute the parent initialization.
def new_input_request(user_input, item_system_prompt, item_goal):
    LogEditorAgent.system_message(item_system_prompt)
    human = f"Extract the goals from the following message: {user_input}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", item_system_prompt),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(item_goal)
    goal_classifier = check_prompt | structured_llm
    goal_class = goal_classifier.invoke({})

    # Convert the Pydantic model to a dictionary
    goal_dict = goal_class.model_dump()

    # Iterate and print names and values
    LogEditorAgent.parsed_goal(f"Parsed Goal Fields: ")
    for key, value in goal_dict.items():
        LogEditorAgent.parsed_goal(f"{key}: {value}")
    LogEditorAgent.parsed_goal(f"")

    return goal_class


class MoveForwardWithSchedule(BaseModel):
    allow_schedule: bool = Field(
        False, description="True ONLY if the user has indicated that they want to move forward with their schedule."
    )


confirm_valid_schedule_edit_prompt = """
You are an expert on conversational analysis. 

A user has been presented with a schedule they have requested and is going to indicate whether or not they would like to continue with this schedule. 

You are to extract the structured information from the user's input regarding whether or not they would like to move forward with this schedule.
"""


confirm_invalid_schedule_edit_prompt = """
You are an expert on conversational analysis. 

A user has been presented with the fact that a schedule they have requested is not recommended and is going to indicate whether or not they would like to continue with this schedule. 

You are to extract the structured information from the user's input regarding whether or not they would like to move forward with this schedule.
"""

# Request permission from user to allow edits that aren't advised.
def does_user_allow_schedule(user_input, is_schedule_invalid=False):
    LogEditorAgent.verbose(f"Extract the confirmation from the following message: {user_input}")

    # Retrieve whether the user wants to move forward with the not reccommended.
    if is_schedule_invalid:
        goal_class = new_input_request(user_input, confirm_invalid_schedule_edit_prompt, MoveForwardWithSchedule)

    else:
        goal_class = new_input_request(user_input, confirm_valid_schedule_edit_prompt, MoveForwardWithSchedule)

    return goal_class.allow_schedule