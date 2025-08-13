from logging_config import LogDBInit
import re

from app import db
from app.models import (
    Exercise_Supportive_Equipment,
    Exercise_Assistive_Equipment,
    Exercise_Weighted_Equipment,
    Exercise_Marking_Equipment,
    Exercise_Other_Equipment,
)
from .utils import determine_connector, extract_number


class Data_Importer:
    # Method to convert the exercise equipment join tables to the proper format.
    def _parse_exercise_join_table(self, exercise_equipment_df, model_type):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.equipment_ids):
            LogDBInit.data_errors("IDs not initialized.")
            return None

        # Create the new column to determine how the equipment should be included.
        exercise_equipment_df["Equipment Relationship"] = exercise_equipment_df["Equipment"].apply(determine_connector)

        # Convert the ' & 's to a list and explode into new rows.
        exercise_equipment_df["Equipment"] = exercise_equipment_df["Equipment"].str.split(' & ')
        exercise_equipment_df = exercise_equipment_df.explode("Equipment", ignore_index=True)

        # Convert the ' | 's to a list and explode into new rows.
        exercise_equipment_df["Equipment"] = exercise_equipment_df["Equipment"].str.split(r" \| ")
        exercise_equipment_df = exercise_equipment_df.explode("Equipment", ignore_index=True)

        # Apply the function to extract the number and store it in a new column
        exercise_equipment_df['Quantity'] = exercise_equipment_df["Equipment"].apply(extract_number)

        # Create the updated column with the number removed from the original string
        exercise_equipment_df["Equipment"] = exercise_equipment_df["Equipment"].apply(lambda x: re.sub(r' \(\d+\)$', '', x))

        # Capitalize to match format of identifier strings
        exercise_equipment_df["Equipment"] = exercise_equipment_df["Equipment"].str.title()

        exercise_equipment_df["Exercise ID"] = exercise_equipment_df["Exercise"].map(self.exercise_ids)
        exercise_equipment_df["Equipment ID"] = exercise_equipment_df["Equipment"].map(self.equipment_ids)

        # Create a list of entries for the exercises
        for _, row in exercise_equipment_df.iterrows():
            db_entry = model_type(
                exercise_id=row["Exercise ID"], 
                equipment_id=row["Equipment ID"],
                quantity=row["Quantity"],
                equipment_relationship=row["Equipment Relationship"],
            )
            db.session.merge(db_entry)
        db.session.commit()

        return exercise_equipment_df

    def exercise_supportive_equipment(self):
        LogDBInit.introductions(f"Initializing Exercise_Supportive_Equipment table.")
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_supportive_equipment_df = self.exercises_df[["Exercise", "Supportive Equipment"]].copy().dropna()
        exercise_supportive_equipment_df.rename(columns={"Supportive Equipment": "Equipment"}, inplace=True)
        exercise_supportive_equipment_df = self._parse_exercise_join_table(exercise_supportive_equipment_df, Exercise_Supportive_Equipment)
        return None

    def exercise_assistive_equipment(self):
        LogDBInit.introductions(f"Initializing Exercise_Assistive_Equipment table.")
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_assistive_equipment_df = self.exercises_df[["Exercise", "Assistive Equipment"]].copy().dropna()
        exercise_assistive_equipment_df.rename(columns={"Assistive Equipment": "Equipment"}, inplace=True)
        exercise_assistive_equipment_df = self._parse_exercise_join_table(exercise_assistive_equipment_df, Exercise_Assistive_Equipment)
        return None

    def exercise_weighted_equipment(self):
        LogDBInit.introductions(f"Initializing Exercise_Weighted_Equipment table.")
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_weighted_equipment_df = self.exercises_df[["Exercise", "Weighted Equipment"]].copy().dropna()
        exercise_weighted_equipment_df.rename(columns={"Weighted Equipment": "Equipment"}, inplace=True)
        exercise_weighted_equipment_df = self._parse_exercise_join_table(exercise_weighted_equipment_df, Exercise_Weighted_Equipment)
        return None

    def exercise_marking_equipment(self):
        LogDBInit.introductions(f"Initializing Exercise_Marking_Equipment table.")
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_marking_equipment_df = self.exercises_df[["Exercise", "Marking Equipment"]].copy().dropna()
        exercise_marking_equipment_df.rename(columns={"Marking Equipment": "Equipment"}, inplace=True)
        exercise_marking_equipment_df = self._parse_exercise_join_table(exercise_marking_equipment_df, Exercise_Marking_Equipment)
        return None

    def exercise_other_equipment(self):
        LogDBInit.introductions(f"Initializing Exercise_Other_Equipment table.")
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_other_equipment_df = self.exercises_df[["Exercise", "Other Equipment"]].copy().dropna()
        exercise_other_equipment_df.rename(columns={"Other Equipment": "Equipment"}, inplace=True)
        exercise_other_equipment_df = self._parse_exercise_join_table(exercise_other_equipment_df, Exercise_Other_Equipment)
        return None

    def run(self):
        self.exercise_supportive_equipment()
        self.exercise_assistive_equipment()
        self.exercise_weighted_equipment()
        self.exercise_marking_equipment()
        self.exercise_other_equipment()
        return None