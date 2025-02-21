from app import db
from sqlalchemy.dialects.postgresql import JSONB

# The equipment that exist.
class Equipment_Library(db.Model):
    __table_args__ = {
        'comment': "The library of equipment that exists."
    }
    # Fields
    __tablename__ = "equipment_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='E.g., Barbell, Dumbbell, Resistance Band')
    
    unit_of_measurement = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., kilograms, centimeters')
    
    # Relationships
    exercises = db.relationship(
        "Exercise_Equipment",
        back_populates = "equipment",
        cascade="all, delete-orphan")

    users = db.relationship(
        "User_Equipment",
        back_populates = "equipment",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "unit_of_measurement": self.unit_of_measurement
        }