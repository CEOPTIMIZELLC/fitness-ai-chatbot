from app import db

class User_Training_Constraints(db.Model):
    """Constraints for a user during a training period."""
    
    # Fields
    __tablename__ = "user_training_constraints"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    max_session_time_minutes = db.Column(
        db.Integer, 
        nullable=False,
        comment='How much time the user has per session in minutes')
    
    days_per_week = db.Column(
        db.Integer, 
        nullable=False,
        comment='Training frequency per week')
    
    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "training_constraints")
    
    available_equipment = db.relationship(
        "User_Training_Available_Equipment",
        back_populates = "training_constraints")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "max_session_time_minutes": self.max_session_time_minutes,
            "days_per_week": self.days_per_week
        }