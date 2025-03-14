from app import db
from .equipment_library import Equipment_Library
from .exercise_equipment import Exercise_Equipment
from .exercise_library import Exercise_Library
from .goal_library import Goal_Library
from .goal_phase_requirements import Goal_Phase_Requirements
from .phase_components_library import Phase_Components_Library
from .phase_components_component_library import Phase_Components_Component_Library
from .phase_components_subcomponent_library import Phase_Components_Subcomponent_Library
from .phase_library import Phase_Library
from .user_equipment import User_Equipment
from .user_macrocycles import User_Macrocycles
from .user_mesocycles import User_Mesocycles
from .users import Users

__all__ = [
    "Equipment_Library",
    "Exercise_Equipment",
    "Exercise_Library",
    "Goal_Library",
    "Goal_Phase_Requirements",
    "Phase_Components_Library",
    "Phase_Components_Component_Library",
    "Phase_Library",
    "Phase_Components_Subcomponent_Library",
    "User_Equipment",
    "User_Macrocycles",
    "User_Mesocycles",
    "Users"
    ] 

tables_dict = {table.__tablename__: table for table in db.Model.__subclasses__()}

def table_object(table_name):
    return tables_dict.get(table_name)
