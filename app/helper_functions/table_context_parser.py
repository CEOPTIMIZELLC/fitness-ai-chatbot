# %%


# %%
# sql_agent.py

from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
#from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from sqlalchemy import text
from langgraph.graph import StateGraph, END
from flask_login import current_user
from flask import current_app

from app import db
from app.models import Users
from app.helper_functions.table_schema_cache import get_database_schema

class AgentState(TypedDict):
    question: str
    subjects: str
    query_result: str
    current_user: str
    relevance: str


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
    finally:
        db.session.close()
    return state

class CheckRelevance(BaseModel):
    relevance: str = Field(
        description="Indicates whether the question is related to the database schema. 'relevant' or 'not_relevant'."
    )

def check_relevance(state: AgentState):
    question = state["question"]
    #schema = get_database_schema(db)
    schema = current_app.table_schema
    print(f"Checking relevance of the question: {question}")
    system = """You are an assistant that determines whether a given question is related to the following database schema.

Schema:
{schema}

Respond with only "relevant" or "not_relevant".
""".format(schema=schema)
    human = f"Question: {question}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", human),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(CheckRelevance)
    relevance_checker = check_prompt | structured_llm
    relevance = relevance_checker.invoke({})
    state["relevance"] = relevance.relevance
    print(f"Relevance determined: {state['relevance']}")
    return state


def irrelevant_question(state: AgentState):
    state["subjects"] = "No subjects"
    state["query_result"] = "Question is irrelevant."
    print(f"{state['query_result']}")
    return state


class Tagging(BaseModel):
    """Tag the piece of text with particular info."""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")
    language: str = Field(description="language of text (should be ISO 639-1 code)")

def tag_question(state: AgentState):
    question = state["question"]
    current_user = state["current_user"]
    questions = ["I love langchain", "non mi piace questo cibo"]
    for question in questions:
        print(f"Tagging context for user '{current_user}': {question}")

        system = "Think carefully, and then tag the text as instructed"
        convert_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Question: {question}"),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(Tagging)
        tag_generator = convert_prompt | structured_llm
        result = tag_generator.invoke({"question": question})
        state["tags"] = {"sentiment": result.sentiment, "language": result.language}
        print(f"Generated tags: {state['tags']}")
    state["query_result"] = "Nothing"
    return state


from typing import Optional
class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="person's name")
    age: Optional[int] = Field(description="person's age")

class Information(BaseModel):
    """Information to extract."""
    people: List[Person] = Field(description="List of info about people")


def extract_information(state: AgentState):
    question = state["question"]
    current_user = state["current_user"]

    questions = ["Joe is 30, his mom is Martha", f"{current_user} is 15, their mom is Amber"]
    for question in questions:
        print(f"Tagging context for user '{current_user}': {question}")

        system = "Extract the relevant information, if not explicitly provided do not guess. Extract partial info"
        convert_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Question: {question}"),
            ]
        )
        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
        structured_llm = llm.with_structured_output(Information)
        extraction_generator = convert_prompt | structured_llm
        result = extraction_generator.invoke({"question": question})
        state["extracted_information"] = result.people
        print(f"Extracted information: {state['extracted_information']}")
    state["query_result"] = "Nothing"
    return state

class RewrittenQuestion(BaseModel):
    question: str = Field(description="The rewritten question.")

def regenerate_query(state: AgentState):
    question = state["question"]
    print("Regenerating the SQL query by rewriting the question.")
    system = """You are an assistant that reformulates an original question to enable more precise SQL queries. Ensure that all necessary details, such as table joins, are preserved to retrieve complete and accurate data.
    """
    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                f"Original Question: {question}\nReformulate the question to enable more precise SQL queries, ensuring all necessary details are preserved.",
            ),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(RewrittenQuestion)
    rewriter = rewrite_prompt | structured_llm
    rewritten = rewriter.invoke({})
    state["question"] = rewritten.question
    print(f"Rewritten question: {state['question']}")
    return state

class TableTagging(BaseModel):
    """Tag the piece of text with particular info."""
    subjects: List[str] = Field(description="sentiment of text, should be `equipment`, `exercises`, or `users`")

def tag_table_question(state: AgentState):
    question = state["question"]
    current_user = state["current_user"]
    print(f"Tagging context for user '{current_user}': {question}")

    system = "Think carefully, and then tag the text as instructed"
    convert_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Question: {question}"),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(TableTagging)
    tag_generator = convert_prompt | structured_llm
    result = tag_generator.invoke({"question": question})
    state["subjects"] = result.subjects
    print(f"Table names: {state['subjects']}")
    return state

class TableNames(BaseModel):
    """Information to extract."""
    tables: List[str] = Field(description="the names of the tables from the schema that should be used")

def retrieve_table_names(state: AgentState):
    question = state["question"]
    current_user = state["current_user"]
    #schema = get_database_schema(db)
    schema = current_app.table_schema
    print(f"Tagging context for user '{current_user}': {question}")

    system = """You are an assistant that retrieves context and extracts relevant information from natural language questions to be used later for SQL queries based on the following schema:

{schema}

The current user is '{current_user}'. Ensure that all query-related data is scoped to this user.

Provide only the tagging without any explanations.

.
""".format(schema=schema, current_user=current_user)
    convert_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Question: {question}"),
        ]
    )
    llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"], temperature=0)
    structured_llm = llm.with_structured_output(TableNames)
    tag_generator = convert_prompt | structured_llm
    result = tag_generator.invoke({"question": question})
    state["tables"] = result.tables
    state["query_result"] = result.tables
    print(f"Table names: {state['tables']}")
    return state

def relevance_router(state: AgentState):
    if state["relevance"].lower() == "relevant":
        return "tag_table_question"
    else:
        return "irrelevant_question"

workflow = StateGraph(AgentState)

workflow.add_node("get_current_user", get_current_user)
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("tag_question", tag_question)
workflow.add_node("extract_information", extract_information)
workflow.add_node("regenerate_query", regenerate_query)
workflow.add_node("irrelevant_question", irrelevant_question)
workflow.add_node("tag_table_question", tag_table_question)
workflow.add_node("retrieve_table_names", retrieve_table_names)

workflow.add_edge("get_current_user", "check_relevance")

workflow.add_conditional_edges(
    "check_relevance",
    relevance_router,
    {
        "tag_table_question": "tag_table_question",
        "irrelevant_question": "irrelevant_question",
    },
)

workflow.add_edge("irrelevant_question", END)
workflow.add_edge("tag_table_question", "retrieve_table_names")
workflow.add_edge("retrieve_table_names", END)

workflow.set_entry_point("get_current_user")

context_retriever_app = workflow.compile()
