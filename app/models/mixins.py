from app import db
from datetime import timedelta
from sqlalchemy.ext.hybrid import hybrid_property

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

class OrderedMixin:
    order = db.Column(
        db.Integer, 
        nullable=False)
