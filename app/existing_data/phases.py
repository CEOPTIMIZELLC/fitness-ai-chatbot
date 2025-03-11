from app.models import Phase_Library
from datetime import timedelta
phases = [
    Phase_Library(id=1, name="Stabilization Endurance", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=6)),
    Phase_Library(id=2, name="Strength Endurance", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(id=3, name="Hypertrophy", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(id=4, name="Maximal Strength", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(id=5, name="Power", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4))
]