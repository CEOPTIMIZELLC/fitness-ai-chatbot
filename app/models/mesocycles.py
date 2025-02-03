from app import db

from sqlalchemy.dialects.postgresql import TEXT

class Mesocycle_Info(db.Model):
    __tablename__ = "mesocycle_info"

    # Fields 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    recommended_duration_weeks = db.Column(
        db.Integer, 
        nullable=False)
    
    recommended_volume_sets = db.Column(
        db.Integer, 
        nullable=False,
        comment='Typical sets per muscle group per week')
    
    rep_range = db.Column(
        db.String, 
        nullable=False, 
        comment='E.g., 6-12 for hypertrophy, 3-6 for strength')
    
    intensity_percentage = db.Column(
        db.String, 
        nullable=False, 
        comment='E.g., 60-75% 1RM for hypertrophy')
    
    key_focus = db.Column(
        TEXT, 
        nullable=False, 
        comment='Primary adaptation goal (e.g., muscle growth, endurance)')
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "recommended_duration_weeks": self.recommended_duration_weeks,
            "recommended_volume_sets": self.recommended_volume_sets,
            "rep_range": self.rep_range,
            "intensity_percentage": self.intensity_percentage,
            "key_focus": self.key_focus
        }