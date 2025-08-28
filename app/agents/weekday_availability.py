from logging_config import LogSolver

from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from flask import current_app

class AgentState(TypedDict):
    new_availability: str
    goal_types: list
    attempts: int
    weekday_availability_llm: str
    weekday_availability: list
    sql_error: bool



from typing import Optional
class Availability(BaseModel):
    """The availability for each workday."""
    monday_availability: Optional[int] = Field(description="availability in seconds for Monday")
    tuesday_availability: Optional[int] = Field(description="availability in seconds for Tuesday")
    wednesday_availability: Optional[int] = Field(description="availability in seconds for Wednesday")
    thursday_availability: Optional[int] = Field(description="availability in seconds for Thursday")
    friday_availability: Optional[int] = Field(description="availability in seconds for Friday")
    saturday_availability: Optional[int] = Field(description="availability in seconds for Saturday")
    sunday_availability: Optional[int] = Field(description="availability in seconds for Sunday")


def weekday_availability_extraction(state: AgentState):
    LogSolver.agent_steps(f"Availability Subagent: Checking classification of the availability.")
    new_availability = state["new_availability"]

    LogSolver.verbose(f"Checking classification of the following availability: {new_availability}")
    system = """You are an assistant that extracts the relevant information, if not explicitly provided, do not guess. Extract partial information.

Some availabilities may be given in minutes or hours. You should convert these to seconds before storing them. 
Example Input: "I am available on Friday for four hours and I am available on Tueday for 30 minutes."
Example Output: tuesday_availability = 1800, friday_availability = 14400

Sometimes, it will be specified that there is no availability on a day or that there is an availability of 0. If this is the case, extract nothing for these days.
Example Input: "I will not be available on Saturdays, Sundays, or Mondays. I am available on Thursday for 2 hours. I will be available on Wednesday for 30 minutes. Oh yeah, and I'll be available for 0 seconds on Tuesday."
Example Output: wednesday_availability = 1800, thursday_availability = 7200

The minimum allowed availability is 15 minutues. If an availability less than that is requested, extract nothing for these days.
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
    weekday_availability_extractor = check_prompt | structured_llm
    result = weekday_availability_extractor.invoke({})
    state["weekday_availability_llm"] = result
    LogSolver.verbose(f"Relevance determined: {state['weekday_availability_llm']}")
    return state

def llm_output_to_timedelta(state: AgentState):
    LogSolver.agent_steps("Availability Subagent: Retrieving the ID of the goal class.")
    weekday_availability_llm = state["weekday_availability_llm"]
    result = []
    for id, availability in enumerate(weekday_availability_llm):
        if availability[1]:
            result.append({"weekday_id": id, "availability": availability[1]})
        else:
            result.append({"weekday_id": id, "availability": 0})

    from calendar import day_name
    for day in result:
        total_seconds = day["availability"]
        LogSolver.verbose(f"{day_name[day["weekday_id"]]}: {total_seconds // 60} minutes and {total_seconds % 60} seconds")

    state["weekday_availability"] = result
    return state

def create_weekday_availability_extraction_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("weekday_availability_extraction", weekday_availability_extraction)
    workflow.add_node("llm_output_to_timedelta", llm_output_to_timedelta)

    workflow.add_edge("weekday_availability_extraction", "llm_output_to_timedelta")
    workflow.add_edge("llm_output_to_timedelta", END)

    workflow.set_entry_point("weekday_availability_extraction")

    return workflow.compile()
