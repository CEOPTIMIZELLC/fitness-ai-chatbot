from app import db
from app.models import Weekday_Library

class Data_Importer:
    def weekdays(self):
        from calendar import day_name
        for i, name in enumerate(day_name):
            db_entry = Weekday_Library(id=i, name=name)
            db.session.merge(db_entry)
        db.session.commit()
        return None