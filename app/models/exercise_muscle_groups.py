from app import db

class Exercise_Muscle_Groups(db.Model):
    __table_args__ = {
        'comment': "The join table for exercises and muscle groups."
    }
    # Fields
    __tablename__ = "exercise_muscle_groups"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    muscle_group_id = db.Column(db.Integer, db.ForeignKey("muscle_group_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "muscle_groups")

    muscle_groups = db.relationship(
        "Muscle_Group_Library",
        back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "muscle_group_id": self.muscle_group_id,
            "muscle_group_name": self.muscle_groups.name
        }