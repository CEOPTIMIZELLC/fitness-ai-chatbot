from logging_config import LogGeneral
from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.impact_goal_models.main_agent import RoutineImpactGoals
from app.goal_prompts.main_agent import goal_extraction_system_prompt
from app.utils.global_variables import sub_agent_names

# Request permission from user to execute the parent initialization.
def new_input_request(user_input, item_system_prompt, item_goal):
    LogGeneral.system_message(item_system_prompt)

    human = f"Extract the goals from the following message: {user_input}"
    LogGeneral.human_message(human)

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
    LogGeneral.parsed_goal(f"Parsed Goal Fields: ")
    for key, value in goal_dict.items():
        LogGeneral.parsed_goal(f"{key}: {value}")
    LogGeneral.parsed_goal(f"")

    return goal_class

# Extract the individual item
def _user_input_sub_extraction(state, sub_agent_name, sub_agent_request):
    if not sub_agent_request:
        return state

    # Extract the values from the user request.
    state[f"{sub_agent_name}_is_requested"] = True
    state[f"{sub_agent_name}_detail"] = sub_agent_request
    return state

def user_input_information_extraction(user_input):
    state={}

    goal_class = new_input_request(user_input, goal_extraction_system_prompt, RoutineImpactGoals)
    goal_class_dump = goal_class.model_dump()

    state["attempts"] = 1
    for sub_agent_name in sub_agent_names:
        state = _user_input_sub_extraction(state, sub_agent_name, goal_class_dump[sub_agent_name])

    return state

