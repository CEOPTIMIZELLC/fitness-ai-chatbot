from app import db

class User_Training_Available_Equipment(db.Model):
    """Equipment available to a user during a training period."""

    # Fields
    __tablename__ = "user_training_available_equipment"
    id = db.Column(db.Integer, primary_key=True)
    user_training_constraints_id = db.Column(db.Integer, db.ForeignKey("user_training_constraints.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id"), nullable=False)
    
    # Relationships
    training_constraints = db.relationship(
        "User_Training_Constraints",
        back_populates = "available_equipment")
    
    equipment = db.relationship(
        "Equipment_Library",
        back_populates = "training_available_equipment")
    
    measurements = db.relationship(
        "User_Training_Equipment_Measurements",
        back_populates = "available_equipment")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_training_constraints_id": self.user_training_constraints_id,
            "equipment_name": self.equipment.name
        }