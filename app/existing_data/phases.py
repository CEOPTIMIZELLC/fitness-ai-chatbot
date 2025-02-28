from app.models import Phase_Library
from datetime import timedelta
phases = [
    Phase_Library(name="Stabilization Endurance", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=6)),
    Phase_Library(name="Strength Endurance", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(name="Hypertrophy", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(name="Maximal Strength", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4)),
    Phase_Library(name="Power", 
                  phase_duration_minimum_in_weeks=timedelta(weeks=4), 
                  phase_duration_maximum_in_weeks=timedelta(weeks=4))
]