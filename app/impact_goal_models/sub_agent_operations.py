from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class ReadMode(str, Enum):
    plural = "plural"
    current = "current"

class ReadOperationGoal(BaseModel):
    """Goal extraction from user input regarding if a read operation should be performed."""
    is_requested: bool = Field(
        False, description="True if the user is indicating a desire to read information in their original request."
    )
    read_method: ReadMode = Field(
        None, description="The method that should be performed. Should be None if reading operation isn't requested."
    )
    detail: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the request for reading specifically."
    )

class AlterOperationGoal(BaseModel):
    """Goal extraction from user input regarding if an alter operation should be performed."""
    is_requested: bool = Field(
        False, description="True if the user is indicating a desire to alter an existing item in their database."
    )
    detail: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the request for altering item(s) specifically."
    )

class CreateOperationGoal(BaseModel):
    """Goal extraction from user input regarding if a create operation should be performed."""
    is_requested: bool = Field(
        False, description="True if the user is indicating a desire to create a new item."
    )
    detail: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the request to create item(s) specifically."
    )

class DeleteOperationGoal(BaseModel):
    """Goal extraction from user input regarding if a delete operation should be performed."""
    is_requested: bool = Field(
        False, description="True if the user is indicating a desire to delete an existing item in their database."
    )
    detail: Optional[str] = Field(
        None, description="The portion(s) of the original message that are relevant to the request to delete item(s) specifically."
    )

class OperationGoals(BaseModel):
    """Goal extraction from user input regarding which operation(s) is to be performed."""
    read_request: Optional[ReadOperationGoal] = Field(
        None, description="All information and requests from the original message relating to whether one of the goals is to read."
    )
    alter_request: Optional[AlterOperationGoal] = Field(
        None, description="All information and requests from the original message relating to whether one of the goals is to alter an existing item."
    )
    create_request: Optional[CreateOperationGoal] = Field(
        None, description="All information and requests from the original message relating to whether one of the goals is to create a new item."
    )
    delete_request: Optional[DeleteOperationGoal] = Field(
        None, description="All information and requests from the original message relating to whether one of the goals is to delete an existing item."
    )
