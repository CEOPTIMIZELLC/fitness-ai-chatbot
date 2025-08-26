from app.logging_config import LogDBInit
import pandas as pd
import numpy as np

from app import db
from app.models import Loading_System_Library

class Data_Importer:
    loading_system_ids = {}

    # Read in the sheets
    def __init__(self, xls):
        # Retrieve Loading Systems dataframe and remove NAN values.
        self.loading_systems_df = xls.parse("loading_system")
        self.loading_systems_df.replace(np.nan, None, inplace=True)

    def loading_systems(self):
        LogDBInit.introductions(f"Initializing Loading_System_Library table.")
        # Loading Systems
        # Create list of Loading Systems
        for i, row in self.loading_systems_df.iterrows():
            self.loading_system_ids[row["loading_system"]] = i+1
            db_entry = Loading_System_Library(
                id=i+1, 
                name=row["loading_system"], 
                description=row["Description"])
            db.session.merge(db_entry)
        db.session.commit()
        
        return None

    def run(self):
        self.loading_systems()
        return None