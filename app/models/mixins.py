from app import db
from datetime import timedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TableNameMixin:
    # @classmethod
    # def __tablename__(cls):
    #     return cls.__name__.lower()

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class NameMixin:
    name = db.Column(db.String(255), unique=True, nullable=False)
    
    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()


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

class OrderedMixin:
    order = db.Column(
        db.Integer, 
        nullable=False)
