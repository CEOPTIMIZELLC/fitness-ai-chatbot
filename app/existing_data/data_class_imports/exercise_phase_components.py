from app import db
from app.models import Exercise_Component_Phases

class Data_Importer:
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