from logging_config import log_existing_data_errors
import numpy as np

from app import db
from app.models import (
    Exercise_Body_Regions,
    Exercise_Bodyparts,
    Exercise_Muscle_Groups,
    Exercise_Muscles,
)

class Data_Importer:
    def exercise_muscles(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.muscle_ids):
            log_existing_data_errors("IDs not initialized.")
            return None
        # Retrieve relevant information for target muscle classification for exercises, as well as dropping the None values.
        exercise_muscle_df = self.exercises_df[["Exercise", "Target Muscle"]].copy().dropna()

        # Lowercase to match format of identifier strings
        exercise_muscle_df["Target Muscle"] = exercise_muscle_df["Target Muscle"].str.lower()

        # Create the id columns
        exercise_muscle_df['Exercise ID'] = exercise_muscle_df['Exercise'].map(self.exercise_ids)
        exercise_muscle_df['Target Muscle ID'] = exercise_muscle_df['Target Muscle'].map(self.muscle_ids)

        # Create a list of entries for Exercise Phase Components table.
        for _, row in exercise_muscle_df.iterrows():
            if np.isnan(row["Exercise ID"]) or np.isnan(row["Target Muscle ID"]):
                log_existing_data_errors(row["Exercise"], "has ID of", row["Exercise ID"], "while", row["Target Muscle"], "has id of", row["Target Muscle ID"])
            else:
                db_entry = Exercise_Muscles(
                    exercise_id=row["Exercise ID"], 
                    muscle_id=row["Target Muscle ID"])
                db.session.merge(db_entry)
        db.session.commit()
        return None

    def exercise_muscle_groups(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.muscle_group_ids):
            log_existing_data_errors("IDs not initialized.")
            return None
        # Retrieve relevant information for target muscle group classification for exercises, as well as dropping the None values.
        exercise_muscle_group_df = self.exercises_df[["Exercise", "Target Muscle Group"]].copy().dropna()

        # Lowercase to match format of identifier strings
        exercise_muscle_group_df["Target Muscle Group"] = exercise_muscle_group_df["Target Muscle Group"].str.lower()

        # Create the id columns
        exercise_muscle_group_df['Exercise ID'] = exercise_muscle_group_df['Exercise'].map(self.exercise_ids)
        exercise_muscle_group_df['Target Muscle Group ID'] = exercise_muscle_group_df['Target Muscle Group'].map(self.muscle_group_ids)

        # Create a list of entries for Exercise Phase Components table.
        for _, row in exercise_muscle_group_df.iterrows():
            db_entry = Exercise_Muscle_Groups(
                exercise_id=row["Exercise ID"], 
                muscle_group_id=row["Target Muscle Group ID"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def exercise_body_regions(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.body_region_ids):
            log_existing_data_errors("IDs not initialized.")
            return None
        # Retrieve relevant information for target body region classification for exercises, as well as dropping the None values.
        exercise_body_region_df = self.exercises_df[["Exercise", "Target Body Region"]].copy().dropna()

        # Lowercase to match format of identifier strings
        exercise_body_region_df["Target Body Region"] = exercise_body_region_df["Target Body Region"].str.lower()

        # Create the id columns
        exercise_body_region_df['Exercise ID'] = exercise_body_region_df['Exercise'].map(self.exercise_ids)
        exercise_body_region_df['Target Body Region ID'] = exercise_body_region_df['Target Body Region'].map(self.body_region_ids)

        # Create a list of entries for Exercise Phase Components table.
        for _, row in exercise_body_region_df.iterrows():
            db_entry = Exercise_Body_Regions(
                exercise_id=row["Exercise ID"], 
                body_region_id=row["Target Body Region ID"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def exercise_bodyparts(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.bodypart_ids):
            log_existing_data_errors("IDs not initialized.")
            return None
        # Retrieve relevant information for target general body area classification for exercises, as well as dropping the None values.
        exercise_bodypart_df = self.exercises_df[["Exercise", "Target General Body Area"]].copy().dropna()

        # Lowercase to match format of identifier strings
        exercise_bodypart_df["Target General Body Area"] = exercise_bodypart_df["Target General Body Area"].str.lower()

        # Create the id columns
        exercise_bodypart_df['Exercise ID'] = exercise_bodypart_df['Exercise'].map(self.exercise_ids)
        exercise_bodypart_df['Target General Body Area ID'] = exercise_bodypart_df['Target General Body Area'].map(self.bodypart_ids)

        # Create a list of entries for Exercise Phase Components table.
        for _, row in exercise_bodypart_df.iterrows():
            db_entry = Exercise_Bodyparts(
                exercise_id=row["Exercise ID"], 
                bodypart_id=row["Target General Body Area ID"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def run(self):
        self.exercise_muscles()
        self.exercise_muscle_groups()
        self.exercise_body_regions()
        self.exercise_bodyparts()
        return None