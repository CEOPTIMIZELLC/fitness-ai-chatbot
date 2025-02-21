from app import db

# The exercises that exist.
class Goal_Library(db.Model):
    # Fields
    __tablename__ = "goal_library"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False, 
        comment='E.g., Fat Loss Goal, Hypertrophy Goal, General Sports Performance Goal')
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }
    