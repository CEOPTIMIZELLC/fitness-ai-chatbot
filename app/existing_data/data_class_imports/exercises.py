import pandas as pd
import numpy as np

from app import db
from app.models import Exercise_Library, General_Exercise_Library
from .utils import create_list_of_table_entries, cluster_main

from pydantic import BaseModel, Field

class GeneralExercise(BaseModel):
    """Information to extract."""
    name: str = Field(description="The name of the general exercise that all of the other exercises are variations of.")
    reasoning: str = Field(description="The reasoning behind the choice of name based on the exercises in the group.")

class Data_Importer:
    general_exercise_ids = {}
    exercise_ids = {}

    # Read in the sheets
    def __init__(self, xls):
        # Retrieve Exercises dataframe and remove NAN values.
        self.exercises_df = xls.parse("Exercises")
        self.exercises_df.replace(np.nan, None, inplace=True)
        self.exercises_df.drop_duplicates(subset=["Exercise"], inplace=True)

    def _general_exercises(self):
        # Ensure that the ids neccessary have been initialized.
        if not self.exercise_ids:
            print("IDs not initialized.")
            return None

        system = """You are a helpful assistant trained in fitness and exercise terminology.

    You have been provided a list of exercises that belong to a singular group and have been tasked with generating a name for the general exercise that all of these fall under.

    """

        self.exercises_df = cluster_main(
            df=self.exercises_df, 
            name_column="Exercise", 
            structured_output_class=GeneralExercise, 
            system_message=system)
        
        # Get all of the names of the general exercises and create entries for each.
        general_exercise_names = self.exercises_df['General Exercise'].unique()
        self.general_exercise_ids = create_list_of_table_entries(self.general_exercise_ids, general_exercise_names, General_Exercise_Library)

        # Map the General Exercise ID to the Exercise
        self.exercises_df['General Exercise ID'] = self.exercises_df['General Exercise'].map(self.general_exercise_ids)

        return None

    def _exercises(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.general_exercise_ids):
            print("IDs not initialized.")
            return None

        # Create a list of entries for the exercises
        for i, row in self.exercises_df.iterrows():
            db_entry = Exercise_Library(
                id=row["Exercise ID"], 
                general_exercise_id=row["General Exercise ID"], 
                name=row["Exercise"], 
                base_strain=row["Base Strain"], 
                technical_difficulty=row["Technical Difficulty"], 
                tags=row["Tags"], 
                sides=row["Sides"], 
                body_position=row["Body Position"], 
                option_for_added_weight=row["Option for added weight"], 
                # is_weighted=pd.notna(row["Weighted Equipment"]),
                proprioceptive_progressions=row["Proprioceptive Progressions"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def general_exercises_and_exercises(self):
        # Create the dictionary of ids.
        for i, row in self.exercises_df.iterrows():
            self.exercise_ids[row["Exercise"]] = i+1

        self.exercises_df['Exercise ID'] = self.exercises_df['Exercise'].map(self.exercise_ids)
        self._general_exercises()
        self._exercises()
        return None

    def run(self):
        self.general_exercises_and_exercises()
        return None