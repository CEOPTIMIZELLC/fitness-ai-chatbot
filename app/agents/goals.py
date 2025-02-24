# %%


# %%
# sql_agent.py

from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from langgraph.graph import StateGraph, END
from flask_login import current_user
from flask import current_app

from app import db
from app.models import Users, Goal_Library
#from app.helper_functions.table_schema_cache import get_database_schema


class AgentState(TypedDict):
    new_goal: str
    goal_types: list
    current_user: str
    attempts: int
    goal_class: str
    sql_error: bool

class GetCurrentUser(BaseModel):
    current_user: str = Field(
        description="The name of the current user based on the provided user ID."
    )

def get_current_user(state: AgentState):
    print("Retrieving the current user based on user ID.")
    user_id = current_user.id
    
    if not user_id:
        state["current_user"] = "User not found"
        print("No user ID provided in the configuration.")
        return state

    try:
        user = db.session.query(Users).filter(Users.id == int(user_id)).first()
        if user:
            state["current_user"] = user.first_name
            print(f"Current user set to: {state['current_user']}")
        else:
            state["current_user"] = "User not found"
            print("User not found in the database.")
    except Exception as e:
        state["current_user"] = "Error retrieving user"
        print(f"Error retrieving user: {str(e)}")
    return state

# State to retrieve possible goal types.
def retrieve_goal_types(state: AgentState):
    goals = (
        db.session.query(
            Goal_Library.name
        )
        .group_by(Goal_Library.name)
        .all()
    )

    state["goal_types"] = [goal.name.lower() for goal in goals]
    return state


class GoalClassification(BaseModel):
    goal_class: str = Field(
        description="Indicates which goal type the goal should be classified as. Must be one of the goal types provided."
    )

def goal_classification(state: AgentState):
    new_goal = state["new_goal"]
    goal_types = state["goal_types"]

    goal_types_stringified = ", ".join(f'"{s}"' for s in goal_types)

    print(f"Checking classification of the following goal: {new_goal}")
    system = """You are an assistant that determines what goal type a given goal falls into of the following types:

Goal Types:
{goal_types}

Goals may not explicitly state that they are of a certain type, and may need to be inferred.

A goal my not explicitly use the terms that are within the name of a goal. A goal that expresses an interest in weight loss would fall under the category of fat loss, for instance.

A goal may not explicitly state that they want to lose fat, but rather express a target weight or dissatisfaction with a current weight. 

Example: "I would like to only weight 100 lbs." would be a "fat loss goal". 

Respond only with {goal_types}. 
""".format(goal_types=goal_types_stringified)
    human = f"New_goal: {new_goal}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(GoalClassification)
    goal_classifier = check_prompt | structured_llm
    goal_class = goal_classifier.invoke({})
    state["goal_class"] = goal_class.goal_class
    print(f"Relevance determined: {state['goal_class']}")
    return state

def goal_type_to_id(state: AgentState):
    print("Retrieving the ID of the goal class.")

    if not current_user.goal:
        state["goal_id"] = "Goal ID not found"
        print("No goal provided for goal type.")
        return state

    try:
        goal_id = (
            db.session.query(
                Goal_Library.id
            )
            .filter(
                Goal_Library.name.ilike(f'%{state["goal_class"]}%')
            )
            .first()
        )
        # Set the goal and goal id for the user if one is present.
        if goal_id:
            state["goal_id"] = goal_id.id
            current_user.goal = state["new_goal"]
            current_user.goal_id = state["goal_id"]
            db.session.commit()
            print(f"Current goal id is: {state['goal_id']}")
        else:
            state["goal_id"] = "Goal not found"
            print("Goal not found in the database.")
    except Exception as e:
        state["goal_id"] = "Error retrieving goal"
        print(f"Error retrieving goal: {str(e)}")
    return state


workflow = StateGraph(AgentState)

workflow.add_node("get_current_user", get_current_user)
workflow.add_node("retrieve_goal_types", retrieve_goal_types)
workflow.add_node("goal_classification", goal_classification)
workflow.add_node("goal_type_to_id", goal_type_to_id)

workflow.add_edge("get_current_user", "retrieve_goal_types")
workflow.add_edge("retrieve_goal_types", "goal_classification")
workflow.add_edge("goal_classification", "goal_type_to_id")

workflow.add_edge("goal_type_to_id", END)

workflow.set_entry_point("get_current_user")

goal_app = workflow.compile()
