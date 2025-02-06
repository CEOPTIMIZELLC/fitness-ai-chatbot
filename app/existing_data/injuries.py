from app.models import Injury_Library, Severity_Library, Injury_Severity
from datetime import timedelta

'''
injuries = [
    Injury_Library(name="Headache", severity={"mild": timedelta(weeks=2), "moderate": timedelta(weeks=4), "severe": timedelta(weeks=8)}),
    Injury_Library(name="Sprained Ankle", severity={"mild": timedelta(weeks=2), "moderate": timedelta(weeks=4), "severe": timedelta(weeks=8)})
]
'''

month_timedelta = timedelta(days=30)
year_timedelta = timedelta(days=365)

injuries = [
    Injury_Library(name="Headache"),
    Injury_Library(name="Sprained Ankle")
]

serverities = [
    Severity_Library(name="mild"),
    Severity_Library(name="moderate"),
    Severity_Library(name="severe")
]

injury_severities = [
    Injury_Severity(injury_id=1, severity_id=1, estimated_time_to_recovery=timedelta(weeks=2)),
    Injury_Severity(injury_id=1, severity_id=2, estimated_time_to_recovery=timedelta(weeks=4)),
    Injury_Severity(injury_id=1, severity_id=3, estimated_time_to_recovery=timedelta(weeks=8)),
    Injury_Severity(injury_id=2, severity_id=1, estimated_time_to_recovery=timedelta(weeks=1)),
    Injury_Severity(injury_id=2, severity_id=2, estimated_time_to_recovery=timedelta(weeks=2)),
    Injury_Severity(injury_id=2, severity_id=3, estimated_time_to_recovery=timedelta(weeks=4))
]