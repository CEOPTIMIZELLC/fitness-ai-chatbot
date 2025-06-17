from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The exercises that exist.
class General_Exercise_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of general exercises that exists."}

    # Relationships
    exercises = db.relationship(
        "Exercise_Library", 
        back_populates="general_exercises", 
        cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }