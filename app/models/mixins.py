from app import db
from datetime import timedelta
from sqlalchemy.ext.hybrid import hybrid_property


class LibraryMixin:
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(255), 
        unique=True, 
        nullable=False, 
        comment='Name of the entry in the library.')


class JoinTableMixin:
    @classmethod
    def create_relationship(cls, model_class, backref_name, cascade="all, delete-orphan"):
        return db.relationship(
            model_class,
            back_populates=backref_name,
            cascade=cascade
        )

    @classmethod
    def create_foreign_key(cls, table_name, ondelete='CASCADE'):
        return db.Column(
            db.Integer,
            db.ForeignKey(f"{table_name}.id", ondelete=ondelete),
            primary_key=True
        )


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
