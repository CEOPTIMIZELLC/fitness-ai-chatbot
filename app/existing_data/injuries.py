from app.models import Injury_Library, Severity_Library, Injury_Severity

'''
injuries = [
    Injury_Library(name="Headache", severity={"mild": "2 weeks", "moderate": "4 weeks", "severe": "8 weeks"}),
    Injury_Library(name="Sprained Ankle", severity={"mild": "2 weeks", "moderate": "4 weeks", "severe": "8 weeks"})
]
'''

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
    Injury_Severity(injury_id=1, severity_id=1, estimated_time_to_recovery="2 weeks"),
    Injury_Severity(injury_id=1, severity_id=2, estimated_time_to_recovery="4 weeks"),
    Injury_Severity(injury_id=1, severity_id=3, estimated_time_to_recovery="8 weeks"),
    Injury_Severity(injury_id=2, severity_id=1, estimated_time_to_recovery="1 week"),
    Injury_Severity(injury_id=2, severity_id=2, estimated_time_to_recovery="2 week"),
    Injury_Severity(injury_id=2, severity_id=3, estimated_time_to_recovery="4 weeks")
]