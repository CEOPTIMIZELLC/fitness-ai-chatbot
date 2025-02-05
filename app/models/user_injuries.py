from app import db

# The table of injuries that a user currently or previously has.
class User_Injuries(db.Model):
    # Fields
    __tablename__ = "user_injuries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    injury_id = db.Column(db.Integer, db.ForeignKey("injury_library.id"), nullable=False)
    
    severity = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., Mild, Moderate, Severe')
    
    '''
    affected_muscle_groups = db.Column(
        JSONB,
        nullable=False,
        comment='E.g., {"lower_body": true, "upper_body": false}')
    '''
    
    start_date = db.Column(db.Date, nullable=False)
    projected_end_date = db.Column(db.Date, nullable=False)

    actual_end_date = db.Column(
        db.Date,
        nullable=True,
        comment='Filled in when the client fully recovers')
    
    current_status = db.Column(
        db.String(50),
        nullable=False,
        comment='E.g., Recovering, Cleared, Worsened')
    
    status_updated_at = db.Column(
        db.Date,
        nullable=False,
        comment='When the last status update was made')
    
    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "injuries")
    
    injuries = db.relationship(
        "Injury_Library",
        back_populates = "users")
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "injury_name": self.injuries.name,
        }

