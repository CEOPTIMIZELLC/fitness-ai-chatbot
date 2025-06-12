from app import db
import pandas as pd
import numpy as np
from app.models import (
    Body_Region_Library,
    Bodypart_Library,
    Component_Library,
    Equipment_Library,
    Exercise_Library,
    Exercise_Component_Phases,
    Exercise_Body_Regions,
    Exercise_Bodyparts,
    Exercise_Muscle_Groups,
    Exercise_Muscles,
    Exercise_Supportive_Equipment,
    Exercise_Assistive_Equipment,
    Exercise_Weighted_Equipment,
    Exercise_Marking_Equipment,
    Exercise_Other_Equipment,
    Goal_Library,
    Goal_Phase_Requirements,
    Loading_System_Library,
    Muscle_Categories,
    Muscle_Group_Library,
    Muscle_Library,
    Phase_Component_Bodyparts,
    Phase_Component_Library,
    Phase_Library,
    Subcomponent_Library,
    Weekday_Library
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
    loading_system_ids = {}
    phase_ids = {}
    subcomponent_ids = {}
    component_ids = {}
    exercise_ids = {}
    equipment_ids = {}
    plane_of_motion_ids = {}
    equipment_ids = {}

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
        self.loading_systems_df = sheets["loading_system"]
        self.phases_df = sheets["phases"]
        self.subcomponents_df = sheets["periodization_model"]
        self.phase_components_df = sheets["phases_components"]
        self.phase_component_bodyparts_df = sheets["component-phase_bodypart"]
        self.exercises_df = sheets["Exercises"]
        self.exercises_df.drop_duplicates(subset=["Exercise"], inplace=True)
        self.equipment_df = pd.DataFrame(self.exercises_df[["Supportive Equipment", 
                                                            "Assistive Equipment", 
                                                            "Weighted Equipment", 
                                                            "Marking Equipment", 
                                                            "Other Equipment"]].values.ravel(), columns=["Equipment"]).dropna()

    # Create an entry for each weekday.
    def weekdays(self):
        from calendar import day_name
        for i, name in enumerate(day_name):
            db_entry = Weekday_Library(id=i, name=name)
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def loading_systems(self):
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
                # is_weighted=pd.notna(row["Weighted Equipment"]),
                proprioceptive_progressions=row["Proprioceptive Progressions"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def exercise_phase_component(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.component_ids and self.subcomponent_ids):
            print("IDs not initialized.")
            return None
        
        component_ids = {k.title(): v for k, v in self.component_ids.items()}

        # Retrieve relevant information for exercise component-phases, as well as dropping the None values.
        exercise_component_phase_df = self.exercises_df[["Exercise", "Component-Phase"]].copy().dropna()

        # Convert the ' & 's to a list and explode into new rows.
        exercise_component_phase_df["Component-Phase"] = exercise_component_phase_df["Component-Phase"].str.split(' & ')
        exercise_component_phase_df = exercise_component_phase_df.explode("Component-Phase", ignore_index=True)

        # Split the "Component-Phase" column into "Component" and "Subcomponent".
        exercise_component_phase_df[["Component", "Subcomponent"]] = exercise_component_phase_df["Component-Phase"].str.split('-', expand=True)

        # Title case to match format of identifier strings
        exercise_component_phase_df["Component"] = exercise_component_phase_df["Component"].str.title()
        exercise_component_phase_df["Subcomponent"] = exercise_component_phase_df["Subcomponent"].str.title()

        # Create the id columns
        exercise_component_phase_df['Exercise ID'] = exercise_component_phase_df['Exercise'].map(self.exercise_ids)
        exercise_component_phase_df['Component ID'] = exercise_component_phase_df['Component'].map(component_ids)
        exercise_component_phase_df['Subcomponent ID'] = exercise_component_phase_df['Subcomponent'].map(self.subcomponent_ids)

        # Create a list of entries for Exercise Phase Components table.
        for _, row in exercise_component_phase_df.iterrows():
            db_entry = Exercise_Component_Phases(
                exercise_id=row["Exercise ID"], 
                component_id=row["Component ID"],
                subcomponent_id=row["Subcomponent ID"])
            db.session.merge(db_entry)
        db.session.commit()
        return None

    def equipment(self):
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
        return None

    # Method to convert the exercise equipment join tables to the proper format.
    def _parse_exercise_join_table(self, exercise_equipment_df, model_type):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.equipment_ids):
            print("IDs not initialized.")
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
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_supportive_equipment_df = self.exercises_df[["Exercise", "Supportive Equipment"]].copy().dropna()
        exercise_supportive_equipment_df.rename(columns={"Supportive Equipment": "Equipment"}, inplace=True)
        exercise_supportive_equipment_df = self._parse_exercise_join_table(exercise_supportive_equipment_df, Exercise_Supportive_Equipment)
        return None

    def exercise_assistive_equipment(self):
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_assistive_equipment_df = self.exercises_df[["Exercise", "Assistive Equipment"]].copy().dropna()
        exercise_assistive_equipment_df.rename(columns={"Assistive Equipment": "Equipment"}, inplace=True)
        exercise_assistive_equipment_df = self._parse_exercise_join_table(exercise_assistive_equipment_df, Exercise_Assistive_Equipment)
        return None

    def exercise_weighted_equipment(self):
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_weighted_equipment_df = self.exercises_df[["Exercise", "Weighted Equipment"]].copy().dropna()
        exercise_weighted_equipment_df.rename(columns={"Weighted Equipment": "Equipment"}, inplace=True)
        exercise_weighted_equipment_df = self._parse_exercise_join_table(exercise_weighted_equipment_df, Exercise_Weighted_Equipment)
        return None

    def exercise_marking_equipment(self):
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_marking_equipment_df = self.exercises_df[["Exercise", "Marking Equipment"]].copy().dropna()
        exercise_marking_equipment_df.rename(columns={"Marking Equipment": "Equipment"}, inplace=True)
        exercise_marking_equipment_df = self._parse_exercise_join_table(exercise_marking_equipment_df, Exercise_Marking_Equipment)
        return None

    def exercise_other_equipment(self):
        # Copy Information from exercise df and rename the column name for the parser it.
        exercise_other_equipment_df = self.exercises_df[["Exercise", "Other Equipment"]].copy().dropna()
        exercise_other_equipment_df.rename(columns={"Other Equipment": "Equipment"}, inplace=True)
        exercise_other_equipment_df = self._parse_exercise_join_table(exercise_other_equipment_df, Exercise_Other_Equipment)
        return None

    def exercise_muscles(self):
        # Ensure that the ids neccessary have been initialized.
        if not (self.exercise_ids and self.muscle_ids):
            print("IDs not initialized.")
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
                print(row["Exercise"], "has ID of", row["Exercise ID"], "while", row["Target Muscle"], "has id of", row["Target Muscle ID"])
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
            print("IDs not initialized.")
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
            print("IDs not initialized.")
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
            print("IDs not initialized.")
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


def Main(excel_file):
    from pathlib import Path
    file_path = Path(__file__).parent / excel_file
    di = Data_Importer(file_path)
    di.loading_systems()
    di.weekdays()
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
    di.exercise_phase_component()
    di.equipment()
    di.exercise_supportive_equipment()
    di.exercise_assistive_equipment()
    di.exercise_weighted_equipment()
    di.exercise_marking_equipment()
    di.exercise_other_equipment()
    di.exercise_muscles()
    di.exercise_muscle_groups()
    di.exercise_body_regions()
    di.exercise_bodyparts()
    db.session.commit()
    return None

if __name__ == "__main__":
    # Path to the uploaded Excel file
    file_path = "OPT Phase Breakdown.xlsx"
    Main(file_path)