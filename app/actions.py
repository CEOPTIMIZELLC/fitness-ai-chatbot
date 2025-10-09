from config import agent_recursion_limit
from logging_config import log_verbose

from flask import current_app

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from app.utils.global_variables import sub_agent_names, sub_graph_names
from app.utils.list_splitter import separate_by_type

from .graph import create_main_agent_graph

def log_interrupts(snapshot_tasks):
    log_verbose(f"Collect Interrupts")
    interrupt_messages = []
    for snapshot_task in snapshot_tasks:
        if snapshot_task.interrupts:
            interrupt_message_task = snapshot_task.interrupts[0].value["task"]
            for interrupt_message in interrupt_message_task:
                log_verbose(f"Interrupt: {interrupt_message}")
                interrupt_messages.append(interrupt_message)

    # Return an empty list without a header if no interrupts are present.
    if interrupt_messages:
        interrupt_messages = [f"Tasks"] + interrupt_messages

    return [interrupt_messages]

def _log_phase_component_progress(progress_message, listed_schedule):
    for list_item in listed_schedule:
        progress_message.append(list_item)
    return progress_message

def _log_workout_progress(progress_message, listed_schedule):
    separated_data = separate_by_type(listed_schedule)
    separated_dict_data = separated_data[dict]
    warmups = [exercise for exercise in separated_dict_data if exercise["warmup"] == "True"]
    horizontal_exercises = [exercise for exercise in separated_dict_data if not exercise["warmup"] == "True"]
    vertical_exercises = separated_data[list]

    if warmups:
        progress_message.append("Warm-Up Exercises")
        progress_message.append(warmups)

    if horizontal_exercises:
        progress_message.append("\nHorizontal Sets")
        progress_message.append(horizontal_exercises)

    if vertical_exercises:
        for i, vertical_set in enumerate(vertical_exercises, start=1):
            progress_message.append(f"\nVertical Set {i}")
            progress_message.append(vertical_set)
    return progress_message

def log_progress(snapshot_values):
    log_verbose(f"Collect Progress")
    progress_messages = []
    for sub_agent_name in sub_agent_names:
        progress_message = []
        formatted_sub_agent_schedule = snapshot_values.get(f"{sub_agent_name}_formatted", None)
        if formatted_sub_agent_schedule:
            formatted_progress_message = f"{sub_agent_name}: \n{formatted_sub_agent_schedule}"
            log_verbose(f"Formatted Progress: {formatted_progress_message}")

        listed_sub_agent_schedule = snapshot_values.get(f"{sub_agent_name}_list_output", [])
        if listed_sub_agent_schedule:
            # list_progress_message = f"{sub_agent_name}: \n{listed_sub_agent_schedule}"
            # log_verbose(f"List Progress: {list_progress_message}")
            progress_message.append(f"{sub_agent_name}: \n")
            if sub_agent_name not in sub_graph_names:
                progress_message.append(listed_sub_agent_schedule)
            elif sub_agent_name == "phase_component":
                progress_message = _log_phase_component_progress(progress_message, listed_sub_agent_schedule)
            elif sub_agent_name == "workout_schedule":
                progress_message = _log_workout_progress(progress_message, listed_sub_agent_schedule)

        if progress_message:
            progress_messages.append(progress_message)

    # Return an empty list without a header if no schedules are present.
    if not progress_messages:
        return []
    return [f"Schedules Generated"] + progress_messages

# Enters the main agent.
def enter_main_agent(user_id):
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # Keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{user_id}"}}

        # Invoke with new macrocycle and possible goal types.
        result = main_agent_app.invoke(
            {"user_id": user_id, "agent_path": []}, 
            config={
                "recursion_limit": agent_recursion_limit,
                "configurable": {
                    "thread_id": f"user-{user_id}",
                }
            })

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)
    return snapshot_of_agent

# Resumes the main agent with user input.
def resume_main_agent(user_id, user_input):
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    # Keep checkpointer alive during invocation
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        main_agent_app = create_main_agent_graph(checkpointer=checkpointer)
        
        thread = {"configurable": {"thread_id": f"user-{user_id}"}}
        snapshot_of_agent = main_agent_app.get_state(thread)

        result = main_agent_app.invoke(
            Command(resume={"user_input": user_input}),
            config=snapshot_of_agent.config
        )

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)

    return snapshot_of_agent
