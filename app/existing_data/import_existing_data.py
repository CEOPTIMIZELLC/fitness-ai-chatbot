from pathlib import Path
import pandas as pd

from app import db
from .data_class_imports import *

class Data_Importer(
    Equipment_Data, 
    Exercise_Equipment_Data, 
    Exercise_MC_Data, 
    Exercise_PC_Data, 
    Exercise_Data, 
    Loading_Systems_Data, 
    MC_Data, 
    PC_Bodyparts_Data, 
    PC_Data, 
    Weekday_Data):

    def __init__(self, xls):
        Equipment_Data.__init__(self, xls)
        Exercise_Data.__init__(self, xls)
        Loading_Systems_Data.__init__(self, xls)
        MC_Data.__init__(self, xls)
        PC_Bodyparts_Data.__init__(self, xls)
        PC_Data.__init__(self, xls)
    
    def run(self):
        self.loading_systems()
        self.weekdays()
        self.muscles()
        self.muscle_groups()
        self.body_regions()
        self.bodyparts()
        self.muscle_categories()
        self.goals()
        self.phases()
        self.components()
        self.subcomponents()
        self.phase_components()
        self.phase_component_bodyparts()
        self.general_exercises_and_exercises()
        self.exercise_phase_component()
        self.equipment()
        self.exercise_supportive_equipment()
        self.exercise_assistive_equipment()
        self.exercise_weighted_equipment()
        self.exercise_marking_equipment()
        self.exercise_other_equipment()
        self.exercise_muscles()
        self.exercise_muscle_groups()
        self.exercise_body_regions()
        self.exercise_bodyparts()

def Main(excel_file):
    from pathlib import Path
    file_path = Path(__file__).parent / excel_file
    xls = pd.ExcelFile(file_path)
    di = Data_Importer(xls)
    di.run()
    db.session.commit()
    return None

if __name__ == "__main__":
    # Path to the uploaded Excel file
    file_path = "OPT Phase Breakdown.xlsx"
    Main(file_path)