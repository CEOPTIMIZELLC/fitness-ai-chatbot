from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The equipment that exist.
class Equipment_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of equipment that exists."}
    # Fields
    unit_of_measurement = db.Column(
        db.String(50), 
        nullable=True, 
        comment='E.g., kilograms, centimeters')
    
    # Relationships
    supportive_for_exercises = db.relationship(
        "Exercise_Supportive_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    assistive_for_exercises = db.relationship(
        "Exercise_Assistive_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    weighted_for_exercises = db.relationship(
        "Exercise_Weighted_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    marking_for_exercises = db.relationship(
        "Exercise_Marking_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    other_for_exercises = db.relationship(
        "Exercise_Other_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    users = db.relationship(
        "User_Equipment", 
        back_populates="equipment", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "unit_of_measurement": self.unit_of_measurement
        }