from logging_config import LogDBInit, log_existing_data_errors
import numpy as np
from datetime import timedelta

from app import db
from app.models import (
    Component_Library,
    Goal_Library,
    Goal_Phase_Requirements,
    Phase_Component_Library,
    Phase_Library,
    Subcomponent_Library,
)
from .utils import create_list_of_table_entries

class Data_Importer:
    goal_ids = {}
    phase_ids = {}
    subcomponent_ids = {}
    component_ids = {}

    # Read in the sheets
    def __init__(self, xls):
        # Retrieve the phase component dataframes and remove NAN values.
        self.phases_df = xls.parse("phases")
        self.phases_df.replace(np.nan, None, inplace=True)

        self.subcomponents_df = xls.parse("periodization_model")
        self.subcomponents_df.replace(np.nan, None, inplace=True)

        self.phase_components_df = xls.parse("phases_components")
        self.phase_components_df.replace(np.nan, None, inplace=True)

    def goals(self):
        LogDBInit.introductions(f"Initializing Goal_Library table.")
        # Retrieve the three goal type
        goal_columns = self.phases_df.columns[-3:].tolist()

        self.goal_ids = create_list_of_table_entries(self.goal_ids, goal_columns, Goal_Library)

        # Get last id added.
        unique_goal_index = max(self.goal_ids.values()) + 1

        # Add unique goal
        db_entry = Goal_Library(id=unique_goal_index, name="Unique_Goal")
        self.goal_ids["Unique Goal"]=unique_goal_index
        db.session.merge(db_entry)
        db.session.commit()

    def phases(self):
        LogDBInit.introductions(f"Initializing Phase_Library and Goal_Phase_Requirements table.")
        # Phases, Goal Phase Requirements

        # Retrieve the three goal type
        goal_columns = self.phases_df.columns[-3:].tolist()

        # Insert data into phase_library
        for _, row in self.phases_df.iterrows():
            phase_id = row["Phase No"]
            phase_name = row["phase"]
            self.phase_ids[phase_name] = phase_id
            db_entry = Phase_Library(
                id=phase_id, 
                name=phase_name, 
                phase_duration_minimum_in_weeks=timedelta(weeks=row['phase_weeks_duration_min']), 
                phase_duration_maximum_in_weeks=timedelta(weeks=row['phase_weeks_duration_max']))
            db.session.merge(db_entry)
            for goal in goal_columns:
                row[goal] =  row[goal].split(', ')
                db_entry = Goal_Phase_Requirements(
                    goal_id=self.goal_ids[goal], 
                    phase_id=phase_id, 
                    required_phase=row[goal][0], 
                    is_goal_phase=(row[goal][1] == "True")  # Retrieve boolean value.
                )
                db.session.merge(db_entry)
        db.session.commit()

        return None

    def components(self):
        LogDBInit.introductions(f"Initializing Component_Library table.")
        # Retrieve Components from phase components sheet
        component_names = self.phase_components_df['component'].unique()

        # Create list of Subcomponents
        for i, name in enumerate(component_names):
            self.component_ids[name] = i+1
            db_entry = Component_Library(
                id=i+1, 
                name=name, 
                is_warmup=True if (name.lower() == "flexibility") else False)
            db.session.merge(db_entry)
        db.session.commit()

        return None

    def subcomponents(self):
        LogDBInit.introductions(f"Initializing Subcomponent_Library table.")
        # Subcomponents
        # Create list of Subcomponents
        for i, row in self.subcomponents_df.iterrows():
            self.subcomponent_ids[row["Subcomponent"]] = i+1
            db_entry = Subcomponent_Library(
                id=i+1, 
                name=row["Subcomponent"], 
                density=row["Density"], 
                volume=row["Volume"], 
                load=row["Load"], 
                explanation=row["Explanation"])
            db.session.merge(db_entry)
        db.session.commit()
        
        return None

    def phase_components(self):
        LogDBInit.introductions(f"Initializing Phase_Component_Library table.")
        # Ensure that the ids neccessary have been initialized.
        if not (self.phase_ids and self.component_ids and self.subcomponent_ids):
            log_existing_data_errors("IDs not initialized.")
            return None

        # Split Routine
        self.phase_components_df.columns = self.phase_components_df.columns.str.lower()

        self.phase_components_df["subcomponent"] = self.phase_components_df["subcomponent"].str.title()

        # Replace the names of values with their corresponding ids.
        self.phase_components_df['phase ID'] = self.phase_components_df['phase'].map(self.phase_ids)
        self.phase_components_df['component ID'] = self.phase_components_df['component'].map(self.component_ids)
        self.phase_components_df['subcomponent ID'] = self.phase_components_df['subcomponent'].map(self.subcomponent_ids)

        # Create list of Phase Components
        for i, row in self.phase_components_df.iterrows():
            db_entry = Phase_Component_Library(
                id=i+1, 
                phase_id=row["phase ID"], 
                component_id=row["component ID"], 
                subcomponent_id=row["subcomponent ID"], 
                name=row["name"], 
                reps_min=row["reps_min"], 
                reps_max=row["reps_max"], 
                sets_min=row["sets_min"], 
                sets_max=row["sets_max"], 
                tempo=row["tempo"], 
                seconds_per_exercise=row["seconds_per_exercise"], 
                intensity_min=row["intensity_min"], 
                intensity_max=row["intensity_max"], 
                rest_min=row["rest_min"], 
                rest_max=row["rest_max"], 
                required_every_workout=row["required_every_workout"], 
                required_within_microcycle=row["required_within_microcycle"], 
                frequency_per_microcycle_min=row["frequency_per_microcycle_min"], 
                frequency_per_microcycle_max=row["frequency_per_microcycle_max"], 
                exercises_per_bodypart_workout_min=row["exercises_per_bodypart_workout_min"], 
                exercises_per_bodypart_workout_max=row["exercises_per_bodypart_workout_max"], 
                exercise_selection_note=row["exercise_selection_note"])
            db.session.merge(db_entry)
        db.session.commit()

        return None

    def run(self):
        self.goals()
        self.phases()
        self.components()
        self.subcomponents()
        self.phase_components()
        return None