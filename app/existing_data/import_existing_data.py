from app.logging_config import LogDBInit
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

    def run_parallel_tasks(self, task_classes):
        tasks = [
            task_class.run
            for task_class in task_classes
        ]

        run_parallel_queries(
            tasks, 
            task_args = [self] * len(tasks)
        )
    
    def run(self):
        LogDBInit.introductions(f"Beginning database initialization.")
        self.run_parallel_tasks([
            Loading_Systems_Data, 
            Weekday_Data, 
            MC_Data, 
            PC_Data, 
        ])

        Exercise_Data.run(self)
        Equipment_Data.run(self)

        self.run_parallel_tasks([
            PC_Bodyparts_Data, 
            Exercise_PC_Data, 
            Exercise_Equipment_Data, 
            Exercise_MC_Data, 
        ])

        LogDBInit.introductions(f"Ending database initialization.")
        return None

def Main(excel_file):
    from pathlib import Path
    file_path = Path(__file__).parent / excel_file
    xls = pd.ExcelFile(file_path)
    di = Data_Importer(xls)
    di.run()
    db.session.commit()
    setup_checkpointer()
    return None

if __name__ == "__main__":
    # Path to the uploaded Excel file
    file_path = "OPT Phase Breakdown.xlsx"
    Main(file_path)