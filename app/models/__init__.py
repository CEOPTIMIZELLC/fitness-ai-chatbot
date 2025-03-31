from app import db
from .body_region_library import Body_Region_Library
from .bodypart_library import Bodypart_Library
from .equipment_library import Equipment_Library
from .exercise_library import Exercise_Library
from .exercise_muscle_categories import(
    Exercise_Body_Regions,
    Exercise_Bodyparts,
    Exercise_Muscle_Groups,
    Exercise_Muscles)

from .exercise_equipment import (
    Exercise_Supportive_Equipment, 
    Exercise_Assistive_Equipment, 
    Exercise_Weighted_Equipment, 
    Exercise_Marking_Equipment, 
    Exercise_Other_Equipment)

from .goal_library import Goal_Library
from .goal_phase_requirements import Goal_Phase_Requirements
from .muscle_categories import Muscle_Categories
from .muscle_group_library import Muscle_Group_Library
from .muscle_library import Muscle_Library
from .phase_component_library import Phase_Component_Library
from .phase_component_bodyparts import Phase_Component_Bodyparts
from .component_library import Component_Library
from .subcomponent_library import Subcomponent_Library
from .phase_library import Phase_Library
from .user_equipment import User_Equipment
from .user_macrocycles import User_Macrocycles
from .user_mesocycles import User_Mesocycles
from .user_microcycles import User_Microcycles
from .user_workout_days import User_Workout_Days
from .user_workout_components import User_Workout_Components
from .user_exercises import User_Exercises
from .user_weekday_availability import User_Weekday_Availability
from .weekday_library import Weekday_Library
from .users import Users

__all__ = [
    "Body_Region_Library",
    "Bodypart_Library",
    "Equipment_Library",
    "Exercise_Library",
    "Exercise_Body_Regions",
    "Exercise_Bodyparts",
    "Exercise_Muscle_Groups",
    "Exercise_Muscles",
    "Exercise_Supportive_Equipment",
    "Exercise_Assistive_Equipment",
    "Exercise_Weighted_Equipment",
    "Exercise_Marking_Equipment",
    "Exercise_Other_Equipment",
    "Goal_Library",
    "Goal_Phase_Requirements",
    "Muscle_Categories",
    "Muscle_Group_Library",
    "Muscle_Library",
    "Phase_Component_Library",
    "Phase_Component_Bodyparts",
    "Component_Library",
    "Subcomponent_Library",
    "Phase_Library",
    "User_Equipment",
    "User_Macrocycles",
    "User_Mesocycles",
    "User_Microcycles",
    "User_Workout_Days",
    "User_Workout_Components",
    "User_Exercises",
    "User_Weekday_Availability",
    "Weekday_Library",
    "Users",
    ] 

tables_dict = {table.__tablename__: table for table in db.Model.__subclasses__()}

def table_object(table_name):
    return tables_dict.get(table_name)
