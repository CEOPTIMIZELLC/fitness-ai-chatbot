from app import db

# The goals that exist.
class Goal_Library(db.Model):
    # Fields
    __table_args__ = {
        'comment': "The categories of that a goal may fall in to."
    }
    __tablename__ = "goal_library"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False, 
        comment='E.g., Fat Loss Goal, Hypertrophy Goal, General Sports Performance Goal')
    
    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "goals")
    
    # Relationships
    phases = db.relationship(
        "Goal_Phase_Requirements",
        back_populates = "goals",
        cascade="all, delete-orphan")
    
    def to_dict(self):
        phase_requirements=[]
        phases = self.phases
        for phase in phases:
            phase_requirements.append(phase.to_dict())

        return {
            "id": self.id,
            "name": self.name,
            "phase_requirements": phase_requirements
        }
    