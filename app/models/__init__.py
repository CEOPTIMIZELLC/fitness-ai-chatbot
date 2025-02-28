from app import db
from .equipment_library import Equipment_Library
from .exercise_equipment import Exercise_Equipment
from .exercise_library import Exercise_Library
from .goal_library import Goal_Library
from .goal_phase_requirements import Goal_Phase_Requirements
from .phase_library import Phase_Library
from .user_equipment import User_Equipment
from .user_macrocycles import User_Macrocycles
from .users import Users

__all__ = [
    "Equipment_Library",
    "Exercise_Equipment",
    "Exercise_Library",
    "Goal_Library",
    "Goal_Phase_Requirements",
    "Phase_Library",
    "User_Equipment",
    "User_Macrocycles",
    "Users"
    ] 

tables_dict = {table.__tablename__: table for table in db.Model.__subclasses__()}

def table_object(table_name):
    return tables_dict.get(table_name)
