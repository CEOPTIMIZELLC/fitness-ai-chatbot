from app import db
from app.models.mixins import TableNameMixin

# The phases that exist.
class Goal_Phase_Requirements(db.Model, TableNameMixin):
    __table_args__ = {'comment': "Whether a phase is required or a goal phase for a goal."}
    # Fields
    goal_id = db.Column(db.Integer, db.ForeignKey("goal_library.id"), primary_key=True)
    phase_id = db.Column(db.Integer, db.ForeignKey("phase_library.id"), primary_key=True)

    required_phase = db.Column(
        db.String(50), 
        nullable=False, 
        comment='How required the phase is for the goal. E.g., required, optional, unlikely.')

    is_goal_phase = db.Column(
        db.Boolean, 
        nullable=False, 
        comment='Whether or not the phase is the desired goal phase that should be maximized.')

    # Relationships
    goals = db.relationship("Goal_Library", back_populates="phases")    
    phases = db.relationship("Phase_Library", back_populates="goals")    
    def to_dict(self):
        return {
            "goal_name": self.goals.name, 
            "phase_name": self.phases.name, 
            "required_phase": self.required_phase, 
            "is_goal_phase": self.is_goal_phase
        }