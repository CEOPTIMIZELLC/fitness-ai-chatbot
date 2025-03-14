from app import db
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.ext.hybrid import hybrid_property

# The phases that exist.
class User_Macrocycles(db.Model):
    """The macrocycles belonging to a user. This also acts as a join table between a user and the goal types."""
    # Fields
    __table_args__ = {
        'comment': "Macrocycles that a user currently has or previously had planned out."
    }
    __tablename__ = "user_macrocycles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal_library.id"), nullable=False)
    goal = db.Column(
        TEXT, 
        nullable=False, 
        comment='Goal for the entire macrocycle.')

    start_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp(), 
        nullable=False,
        comment='Date that the macrocycle should start.')

    end_date = db.Column(
        db.Date, 
        default=db.func.current_timestamp() + timedelta(weeks=26), 
        nullable=False,
        comment='Date that the macrocycle should end.')

    # Duration of the macrocycle based on the current start and end date.
    @hybrid_property
    def duration(self):
        return self.end_date - self.start_date

    # Relationships
    users = db.relationship(
        "Users",
        back_populates = "macrocycles")

    goals = db.relationship(
        "Goal_Library",
        back_populates = "macrocycles")

    mesocycles = db.relationship(
        "User_Mesocycles",
        back_populates = "macrocycles",
        cascade="all, delete-orphan")

    def to_dict(self):
        total_duration = self.duration
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_name": self.goals.name,
            "goal_id": self.goal_id,
            "goal": self.goal,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration": f"{total_duration.days // 7} weeks {total_duration.days % 7} days"
        }