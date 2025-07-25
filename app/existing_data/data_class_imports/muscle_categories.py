from logging_config import log_existing_data_errors
import pandas as pd
import numpy as np

from app import db
from app.models import (
    Body_Region_Library,
    Bodypart_Library,
    Muscle_Categories,
    Muscle_Group_Library,
    Muscle_Library,
)
from .utils import create_list_of_table_entries

class Data_Importer:
    muscle_ids = {}
    muscle_group_ids = {}
    body_region_ids = {}
    bodypart_ids = {}

    # Read in the sheets
    def __init__(self, xls):
        # Retrieve Muscle Groups dataframe and remove NAN values.
        self.muscle_groups_df = xls.parse("Muscle Groups")
        self.muscle_groups_df.replace(np.nan, None, inplace=True)

    def muscles(self):
        muscle_names = self.muscle_groups_df['Muscle'].unique()
        self.muscle_ids = create_list_of_table_entries(self.muscle_ids, muscle_names, Muscle_Library)
        return None

    def muscle_groups(self):
        muscle_group_names = self.muscle_groups_df['Muscle Group'].unique()
        self.muscle_group_ids = create_list_of_table_entries(self.muscle_group_ids, muscle_group_names, Muscle_Group_Library)
        return None

    def body_regions(self):
        body_region_names = self.muscle_groups_df['Body Region'].unique()
        self.body_region_ids = create_list_of_table_entries(self.body_region_ids, body_region_names, Body_Region_Library)
        return None

    def bodyparts(self):
        general_body_area_names = self.muscle_groups_df['General Body Area (Resistance Phase Component)'].unique()
        self.bodypart_ids = create_list_of_table_entries(self.bodypart_ids, general_body_area_names, Bodypart_Library)
        return None

    def muscle_categories(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.muscle_ids and self.muscle_group_ids and self.body_region_ids and self.bodypart_ids):
            log_existing_data_errors("IDs not initialized.")
            return None

        # Replace the names of values with their corresponding ids.
        self.muscle_groups_df['Muscle ID'] = self.muscle_groups_df['Muscle'].map(self.muscle_ids)
        self.muscle_groups_df['Muscle Group ID'] = self.muscle_groups_df['Muscle Group'].map(self.muscle_group_ids)
        self.muscle_groups_df['Body Region ID'] = self.muscle_groups_df['Body Region'].map(self.body_region_ids)
        self.muscle_groups_df['General Body Area ID'] = self.muscle_groups_df['General Body Area (Resistance Phase Component)'].map(self.bodypart_ids)

        # Create list of Phase Components
        for i, row in self.muscle_groups_df.iterrows():
            db_entry = Muscle_Categories(
                id=i+1,
                muscle_id=row["Muscle ID"], 
                muscle_group_id=row["Muscle Group ID"], 
                body_region_id=row["Body Region ID"], 
                bodypart_id=row["General Body Area ID"])
            db.session.merge(db_entry)
        db.session.commit()
        
        return None

    def run(self):
        self.muscles()
        self.muscle_groups()
        self.body_regions()
        self.bodyparts()
        self.muscle_categories()
        return None