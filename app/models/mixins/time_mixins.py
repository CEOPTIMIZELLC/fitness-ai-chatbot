from app import db
from datetime import timedelta
from sqlalchemy.ext.hybrid import hybrid_property


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class DurationMixin:
    @hybrid_property
    def duration_in_weeks(self):
        return (self.end_date - self.start_date).days // 7
    
    @hybrid_property
    def duration_formatted(self):
        total_duration = self.end_date - self.start_date
        return f"{total_duration.days // 7} weeks {total_duration.days % 7} days"


class DateRangeMixin:
    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False)
    
    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=4), 
        nullable=False)

    @hybrid_property
    def duration(self):
        return self.end_date - self.start_date
