from app.logging_config import LogDBInit
from app.db_session import session_scope
from app.models import Weekday_Library

class Data_Importer:
    def weekdays(self):
        LogDBInit.introductions(f"Initializing Weekday_Library table.")
        from calendar import day_name
        with session_scope() as s:
            for i, name in enumerate(day_name):
                db_entry = Weekday_Library(id=i, name=name)
                s.merge(db_entry)
            # s.commit()
        LogDBInit.introductions(f"Initialized Weekday_Library table.")
        return None

    def run(self):
        self.weekdays()
        return None