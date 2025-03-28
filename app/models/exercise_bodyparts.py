from app import db

class Exercise_Bodyparts(db.Model):
    __table_args__ = {
        'comment': "The join table for exercises and bodyparts."
    }
    # Fields
    __tablename__ = "exercise_bodyparts"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "bodyparts")

    bodyparts = db.relationship(
        "Bodypart_Library",
        back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "bodypart_id": self.bodypart_id,
            "bodypart_name": self.bodyparts.name
        }