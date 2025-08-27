from app.logging_config import LogDBInit
import numpy as np

from app.db_session import session_scope
from app.models import Phase_Component_Bodyparts

class Data_Importer:
    # Read in the sheets
    def __init__(self, xls):
        # Retrieve Phase Component Bodyparts dataframe and remove NAN values.
        self.phase_component_bodyparts_df = xls.parse("component-phase_bodypart")
        self.phase_component_bodyparts_df.replace(np.nan, None, inplace=True)

    def phase_component_bodyparts(self):
        LogDBInit.introductions(f"Initializing Phase_Component_Bodyparts table.")
        # Ensure that the ids neccessary have been initialized.
        if not (self.phase_ids and self.component_ids and self.bodypart_ids):
            LogDBInit.data_errors("IDs not initialized.")
            return None

        # Capitalize to match format of identifier strings
        self.phase_component_bodyparts_df["phase"] = self.phase_component_bodyparts_df["phase"].str.title()
        self.phase_component_bodyparts_df["component"] = self.phase_component_bodyparts_df["component"].str.title()

        # Replace the names of values with their corresponding ids.
        self.phase_component_bodyparts_df['phase ID'] = self.phase_component_bodyparts_df['phase'].map(self.phase_ids)
        self.phase_component_bodyparts_df['component ID'] = self.phase_component_bodyparts_df['component'].map(self.component_ids)
        self.phase_component_bodyparts_df['bodypart ID'] = self.phase_component_bodyparts_df['bodypart'].map(self.bodypart_ids)

        # Create a list of entries for the Phase Component Bodyparts table
        with session_scope() as s:
            for i, row in self.phase_component_bodyparts_df.iterrows():
                db_entry = Phase_Component_Bodyparts(
                    id=i+1, 
                    phase_id=row["phase ID"], 
                    component_id=row["component ID"], 
                    bodypart_id=row["bodypart ID"], 
                    required_within_microcycle=row["Required in a microcycle"])
                s.merge(db_entry)
            # s.commit()
        LogDBInit.introductions(f"Initialized Phase_Component_Bodyparts table.")
        return None

    def run(self):
        self.phase_component_bodyparts()
        return None