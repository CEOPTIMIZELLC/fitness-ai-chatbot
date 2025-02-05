from app import db

class User_Training_Equipment_Measurements(db.Model):
    """Equipment available to a user during a training period."""

    # Fields
    __tablename__ = "user_training_equipment_measurements"
    user_equipment_id = db.Column(db.Integer, db.ForeignKey("user_training_available_equipment.id"), primary_key=True)
    measurement_id = db.Column(db.Integer, db.ForeignKey("measurement_types.id"), primary_key=True)
    measurement = db.Column(db.Integer, nullable=False, comment='The quantitative value of the measurement for the user equipment.')

    # Relationships
    measurements = db.relationship(
        "Measurement_Types",
        back_populates = "training_equipment")
    
    available_equipment = db.relationship(
        "User_Training_Available_Equipment",
        back_populates = "measurements")
    
    def to_dict(self):
        return {
            "measurement_name": self.measurements.name,
            "measurement_unit": self.measurements.unit,
            "equipment_name": self.equipment.name
        }