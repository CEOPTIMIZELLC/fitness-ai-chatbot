from logging_config import LogDBInit
import pandas as pd
import numpy as np
import re

from app.models import Equipment_Library
from .utils import create_list_of_table_entries

class Data_Importer:
    equipment_ids = {}

    # Read in the sheets
    def __init__(self, xls):
        # Retrieve Exercises dataframe and remove NAN values.
        self.exercises_df = xls.parse("Exercises")
        self.exercises_df.replace(np.nan, None, inplace=True)
        self.exercises_df.drop_duplicates(subset=["Exercise"], inplace=True)

        self.equipment_df = pd.DataFrame(self.exercises_df[["Supportive Equipment", 
                                                            "Assistive Equipment", 
                                                            "Weighted Equipment", 
                                                            "Marking Equipment", 
                                                            "Other Equipment"]].values.ravel(), columns=["Equipment"]).dropna()

    def equipment(self):
        LogDBInit.introductions(f"Initializing Equipment table.")
        # Convert the ' & 's to a list and explode into new rows.
        self.equipment_df["Equipment"] = self.equipment_df["Equipment"].str.split(' & ')
        self.equipment_df = self.equipment_df.explode("Equipment", ignore_index=True)

        # Convert the ' | 's to a list and explode into new rows.
        self.equipment_df["Equipment"] = self.equipment_df["Equipment"].str.split(r" \| ")
        self.equipment_df = self.equipment_df.explode("Equipment", ignore_index=True)

        # Remove the quantity of original string
        self.equipment_df["Equipment"] = self.equipment_df["Equipment"].apply(lambda x: re.sub(r' \(\d+\)$', '', x))

        # Capitalize to match format of identifier strings
        self.equipment_df["Equipment"] = self.equipment_df["Equipment"].str.title()

        # Retrieve the unique equipment
        equipment_names = self.equipment_df["Equipment"].unique()

        self.equipment_ids = create_list_of_table_entries(self.equipment_ids, equipment_names, Equipment_Library)
        LogDBInit.introductions(f"Initialized Equipment table.")
        return None
    
    def run(self):
        self.equipment()
        return None