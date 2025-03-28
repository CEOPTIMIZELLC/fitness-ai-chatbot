from app import db

class Exercise_Body_Regions(db.Model):
    __table_args__ = {
        'comment': "The join table for exercises and body regions."
    }
    # Fields
    __tablename__ = "exercise_body_regions"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    body_region_id = db.Column(db.Integer, db.ForeignKey("body_region_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship(
        "Exercise_Library",
        back_populates = "body_regions")

    body_regions = db.relationship(
        "Body_Region_Library",
        back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "body_region_id": self.body_region_id,
            "body_region_name": self.body_regions.name
        }