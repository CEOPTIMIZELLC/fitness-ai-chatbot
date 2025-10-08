from config import agent_recursion_limit
from logging_config import log_verbose

from flask import current_app

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt, Command

from app.utils.global_variables import sub_agent_names

from .graph import create_main_agent_graph

def log_interrupts(snapshot_tasks):
    interrupt_messages = []
    for snapshot_task in snapshot_tasks:
        if snapshot_task.interrupts:
            interrupt_message = snapshot_task.interrupts[0].value["task"]
            interrupt_messages.append(interrupt_message)
            log_verbose(f"Interrupt: {interrupt_message}")
    return interrupt_messages

def log_progress(state):
    progress_messages = [f"Schedule Generated."]
    for sub_agent_name in sub_agent_names:
        formatted_sub_agent_schedule = state.get(f"{sub_agent_name}_formatted", None)
        if formatted_sub_agent_schedule:
            progress_message = f"{sub_agent_name}: \n{formatted_sub_agent_schedule}"
            log_verbose(f"Progress: {progress_message}")
            progress_messages.append(progress_message)
    return progress_messages

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

        progress_messages = log_progress(result)

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)

        # Retrieve the current interrupt, if there is one.
        tasks = snapshot_of_agent.tasks
        if tasks:
            interrupt_messages = log_interrupts(snapshot_of_agent.tasks)
        else:
            interrupt_messages = []
    return progress_messages, interrupt_messages

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

        progress_messages = log_progress(result)

        # Retrieve the current state of the agent.
        snapshot_of_agent = main_agent_app.get_state(thread)

        # Retrieve the current interrupt, if there is one.
        tasks = snapshot_of_agent.tasks
        if tasks:
            interrupt_messages = log_interrupts(snapshot_of_agent.tasks)
        else:
            interrupt_messages = []
    return progress_messages, interrupt_messages
