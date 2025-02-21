from app import db

class User_Equipment(db.Model):
    """Equipment available to a user during a training period."""
    __table_args__ = {
        'comment': "The equipment that a user has to be able to perform exercises."
    }

    # Fields
    __tablename__ = "user_equipment"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment_library.id"), nullable=False)
    measurement = db.Column(db.Integer, nullable=False)
    
    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "equipment")
    
    equipment = db.relationship(
        "Equipment_Library",
        back_populates = "users")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "equipment_name": self.equipment.name,
            "measurement": self.measurement,
            "unit_of_measurement": self.equipment.unit_of_measurement
        }