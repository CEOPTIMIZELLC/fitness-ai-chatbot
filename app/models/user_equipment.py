from app import db
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

class User_Equipment(BaseModel, TableNameMixin):
    """Equipment available to a user during a training period."""
    __table_args__ = {'comment': "The equipment that a user has to be able to perform exercises."}

    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id"), nullable=False)
    measurement = db.Column(db.Integer, nullable=False)

    # Relationships
    users = db.relationship("Users", back_populates="equipment")
    equipment = db.relationship("Equipment_Library", back_populates="users")

    def to_dict(self):
        return {
            "id": self.id, 
            "user_id": self.user_id, 
            "equipment_name": self.equipment.name, 
            "measurement": self.measurement, 
            "unit_of_measurement": self.equipment.unit_of_measurement
        }