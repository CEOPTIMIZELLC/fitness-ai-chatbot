from logging_config import LogSolver
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from flask import current_app

class AgentState(TypedDict):
    new_goal: str
    goal_types: list
    attempts: int
    goal_class: str
    goal_id: int
    sql_error: bool

class GoalClassification(BaseModel):
    goal_class: str = Field(
        description="Indicates which goal type the goal should be classified as. Must be one of the goal types provided."
    )

def goal_classification(state: AgentState):
    LogSolver.agent_steps("Goal Subagent: Checking classification of the goal.")
    new_goal = state["new_goal"]
    goal_types = state["goal_types"]

    goal_types_stringified = ", ".join(f'"{s["name"]}"' for s in goal_types)

    LogSolver.verbose(f"Checking classification of the following goal: {new_goal}")
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
    LogSolver.verbose(f"Relevance determined: {state['goal_class']}")
    return state

def goal_type_to_id(state: AgentState):
    LogSolver.agent_steps("Goal Subagent: Retrieving the ID of the goal class.")
    goal_types = state["goal_types"]
    goal_class = state["goal_class"]

    try:
        # Retrieve the id of the corresponding goal type.
        goal_id = next(
            (item for item in goal_types if item["name"] == goal_class), 
            None
        )
        
        # Set the goal and goal id for the user if one is present.
        if goal_id:
            state["goal_id"] = goal_id["id"]
            LogSolver.verbose(f"Goal id is: {state['goal_id']}")
        else:
            state["goal_id"] = "Goal not found"
            LogSolver.verbose("Goal not found in the database.")
    except Exception as e:
        state["goal_id"] = "Error retrieving goal"
        LogSolver.verbose(f"Error retrieving goal: {str(e)}")
    return state

def create_goal_classification_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("goal_classification", goal_classification)
    workflow.add_node("goal_type_to_id", goal_type_to_id)

    workflow.add_edge("goal_classification", "goal_type_to_id")

    workflow.add_edge("goal_type_to_id", END)

    workflow.set_entry_point("goal_classification")

    return workflow.compile()
