from app import db
import pandas as pd
import numpy as np
from app.models import (
    Body_Region_Library,
    Bodypart_Library,
    Component_Library,
    Equipment_Library,
    Exercise_Body_Regions,
    Exercise_Bodyparts,
    Exercise_Library,
    Exercise_Muscle_Groups,
    Exercise_Muscles,
    Goal_Library,
    Goal_Phase_Requirements,
    Muscle_Categories,
    Muscle_Group_Library,
    Muscle_Library,
    Phase_Component_Bodyparts,
    Phase_Component_Library,
    Phase_Library,
    Subcomponent_Library
)

from datetime import timedelta
import re

def set_keys_to_lowercase(d):
    return {k.lower(): v for k, v in d.items()}

def create_list_of_table_entries(ids, names, model_type):
    # Create list of Components
    for i, name in enumerate(names, start=1):
        ids[name] = i
        db_entry = model_type(id=i, name=name)

        # Using merge to handle duplicates gracefully
        db.session.merge(db_entry)
    db.session.commit()
    return ids

# Function to determine the connector for new column value
def determine_connector(text):
    if ' & ' in text:
        return 'and'
    elif ' | ' in text:
        return 'or'
    else:
        return None

# Function to extract the number or set it to 1
def extract_number(text):
    # Search for a number inside parentheses at the end of the string
    match = re.search(r"\((\d+)\)$", text)
    if match:
        return int(match.group(1))  # Return the number inside parentheses
    else:
        return 1  # Return 1 if no number is found

class Data_Importer:
    sheets = {}
    muscle_ids = {}
    muscle_group_ids = {}
    body_region_ids = {}
    bodypart_ids = {}
    goal_ids = {}
    phase_ids = {}
    subcomponent_ids = {}
    component_ids = {}
    exercise_ids = {}
    equipment_ids = {}
    plane_of_motion_ids = {}

    # Read in the sheets
    def __init__(self, file_path):
        # Load the Excel file
        xls = pd.ExcelFile(file_path)

        # Read each sheet into a DataFrame
        sheets = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}

        # Display the first few rows of each sheet
        for _, df in sheets.items():
            df.replace(np.nan, None, inplace=True)
        
        # Assign the sheets to variables.
        self.muscle_groups_df = sheets["Muscle Groups"]
        self.phases_df = sheets["phases"]
        self.subcomponents_df = sheets["periodization_model"]
        self.phase_components_df = sheets["phases_components"]
        self.phase_component_bodyparts_df = sheets["component-phase_bodypart"]
        self.exercises_df = sheets["Exercises Copy"]

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
            print("IDs not initialized.")
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

    def phases(self):
        # Goals, Phases, Goal Phase Requirements

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
                row[goal] =  row[goal].split(',')
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
        # Retrieve Components from phase components sheet
        component_names = self.phase_components_df['component'].unique()

        self.component_ids = create_list_of_table_entries(self.component_ids, component_names, Component_Library)
        return None

    def subcomponents(self):
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
        # Ensure that the ids neccessary have been initialized.
        if not (self.phase_ids and self.component_ids and self.subcomponent_ids):
            print("IDs not initialized.")
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

    def phase_component_bodyparts(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.phase_ids and self.component_ids and self.bodypart_ids):
            print("IDs not initialized.")
            return None

        # Capitalize to match format of identifier strings
        self.phase_component_bodyparts_df["phase"] = self.phase_component_bodyparts_df["phase"].str.title()
        self.phase_component_bodyparts_df["component"] = self.phase_component_bodyparts_df["component"].str.title()

        # Replace the names of values with their corresponding ids.
        self.phase_component_bodyparts_df['phase ID'] = self.phase_component_bodyparts_df['phase'].map(self.phase_ids)
        self.phase_component_bodyparts_df['component ID'] = self.phase_component_bodyparts_df['component'].map(self.component_ids)
        self.phase_component_bodyparts_df['bodypart ID'] = self.phase_component_bodyparts_df['bodypart'].map(self.bodypart_ids)

        # Create a list of entries for the Phase Component Bodyparts table
        for i, row in self.phase_component_bodyparts_df.iterrows():
            db_entry = Phase_Component_Bodyparts(
                id=i+1, 
                phase_id=row["phase ID"], 
                component_id=row["component ID"], 
                bodypart_id=row["bodypart ID"], 
                required_within_microcycle=row["Required in a microcycle"])
            db.session.merge(db_entry)
        db.session.commit()

        return None

    def exercises(self):
        # Create a list of entries for the exercises
        for i, row in self.exercises_df.iterrows():
            self.exercise_ids[row["Exercise"]] = i+1
            db_entry = Exercise_Library(
                id=i+1, 
                name=row["Exercise"], 
                base_strain=row["Base Strain"], 
                technical_difficulty=row["Technical Difficulty"], 
                tags=row["Tags"], 
                sides=row["Sides"], 
                body_position=row["Body Position"], 
                option_for_added_weight=row["Option for added weight"], 
                proprioceptive_progressions=row["Proprioceptive Progressions"])
            db.session.merge(db_entry)
        db.session.commit()

        # Add the ids to the join table
        self.exercises_df['Exercise ID'] = self.exercises_df['Exercise'].map(self.exercise_ids)        
        return None

    # Method to convert the exercise equipment join tables to the proper format.
    def parse_exercise_join_table(self, exercise_equipment_df, equipment_column_name):
        # Create the new column
        exercise_equipment_df['Relationship'] = exercise_equipment_df[equipment_column_name].apply(determine_connector)

        # Convert the ' & 's to a list and explode into new rows.
        exercise_equipment_df[equipment_column_name] = exercise_equipment_df[equipment_column_name].str.split(' & ')
        exercise_equipment_df = exercise_equipment_df.explode(equipment_column_name, ignore_index=True)

        # Convert the ' | 's to a list and explode into new rows.
        exercise_equipment_df[equipment_column_name] = exercise_equipment_df[equipment_column_name].str.split(r" \| ")
        exercise_equipment_df = exercise_equipment_df.explode(equipment_column_name, ignore_index=True)

        # Apply the function to extract the number and store it in a new column
        exercise_equipment_df['Quantity'] = exercise_equipment_df[equipment_column_name].apply(extract_number)

        # Create the updated column with the number removed from the original string
        exercise_equipment_df[equipment_column_name] = exercise_equipment_df[equipment_column_name].apply(lambda x: re.sub(r' \(\d+\)$', '', x))

        # Capitalize to match format of identifier strings
        exercise_equipment_df[equipment_column_name] = exercise_equipment_df[equipment_column_name].str.title()

        return exercise_equipment_df

def Main(excel_file):
    from pathlib import Path
    file_path = Path(__file__).parent / excel_file
    di = Data_Importer(file_path)
    di.muscles()
    di.muscle_groups()
    di.body_regions()
    di.bodyparts()
    di.muscle_categories()
    di.phases()
    di.components()
    di.subcomponents()
    di.phase_components()
    di.phase_component_bodyparts()
    di.exercises()
    return None

if __name__ == "__main__":
    # Path to the uploaded Excel file
    file_path = "OPT Phase Breakdown.xlsx"
    Main(file_path)