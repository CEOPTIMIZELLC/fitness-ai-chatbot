
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from langgraph.graph import StateGraph, END
from flask import current_app
from datetime import timedelta

class AgentState(TypedDict):
    new_availability: str
    goal_types: list
    attempts: int
    workout_availability_llm: int
    workout_availability: int
    sql_error: bool



from typing import Optional
class Availability(BaseModel):
    """The availability for each workday."""
    availability: int = Field(description="availability in seconds")


def workout_availability_extraction(state: AgentState):
    new_availability = state["new_availability"]

    print(f"Checking classification of the following availability: {new_availability}")
    system = """You are an assistant that extracts the relevant information, if not explicitly provided, do not guess. Extract partial information.

Some availabilities may be given in minutes or hours. You should convert these to seconds before storing them. 
Example Input: "I am available to workout for four hours. 
Example Output: availability = 1800

Example Input: I am available to workout for 30 minutes."
Example Output: availability = 14400

The maximum allowed availability is 2 hours. If an availability more than that is requested, extract 0.
"""
    human = f"New_availability: {new_availability}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(Availability)
    workout_availability_extractor = check_prompt | structured_llm
    result = workout_availability_extractor.invoke({})
    state["workout_availability_llm"] = result.availability
    print(f"Relevance determined: {state['workout_availability_llm']}")
    return state

def llm_output_to_timedelta(state: AgentState):
    print("Retrieving the ID of the goal class.")
    workout_availability_llm = state["workout_availability_llm"]
    state["workout_availability"] = timedelta(seconds=workout_availability_llm)

    print(f"Workouts can only be {workout_availability_llm // 60} minutes and {workout_availability_llm % 60} seconds long.")
    return state

def create_workout_availability_extraction_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("workout_availability_extraction", workout_availability_extraction)
    workflow.add_node("llm_output_to_timedelta", llm_output_to_timedelta)

    workflow.add_edge("workout_availability_extraction", "llm_output_to_timedelta")

    workflow.add_edge("llm_output_to_timedelta", END)

    workflow.set_entry_point("workout_availability_extraction")

    return workflow.compile()
