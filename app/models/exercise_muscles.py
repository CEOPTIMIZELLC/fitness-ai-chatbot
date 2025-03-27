from app import db

class Exercise_Muscles(db.Model):
    __table_args__ = {
        'comment': "The join table for exercises and muscles."
    }
    # Fields
    __tablename__ = "exercise_muscles"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    muscle_id = db.Column(db.Integer, db.ForeignKey("muscle_library.id", ondelete='CASCADE'), primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False)

    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "muscles")

    muscles = db.relationship(
        "Muscle_Library",
        back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "muscle_id": self.muscle_id,
            "muscle_name": self.muscles.name
        }