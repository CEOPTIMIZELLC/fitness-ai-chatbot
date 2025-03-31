from app import db

class Exercise_Bodyparts(db.Model):
    __table_args__ = {'comment': "The join table for exercises and bodyparts."}

    # Fields
    __tablename__ = "exercise_bodyparts"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates = "bodyparts")
    bodyparts = db.relationship("Bodypart_Library", back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "bodypart_id": self.bodypart_id,
            "bodypart_name": self.bodyparts.name
        }

class Exercise_Body_Regions(db.Model):
    __table_args__ = {'comment': "The join table for exercises and body regions."}

    # Fields
    __tablename__ = "exercise_body_regions"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    body_region_id = db.Column(db.Integer, db.ForeignKey("body_region_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates = "body_regions")
    body_regions = db.relationship("Body_Region_Library", back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "body_region_id": self.body_region_id,
            "body_region_name": self.body_regions.name
        }

class Exercise_Muscle_Groups(db.Model):
    __table_args__ = {'comment': "The join table for exercises and muscle groups."}

    # Fields
    __tablename__ = "exercise_muscle_groups"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    muscle_group_id = db.Column(db.Integer, db.ForeignKey("muscle_group_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates = "muscle_groups")
    muscle_groups = db.relationship("Muscle_Group_Library", back_populates = "exercises")

    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "muscle_group_id": self.muscle_group_id,
            "muscle_group_name": self.muscle_groups.name
        }

class Exercise_Muscles(db.Model):
    __table_args__ = {'comment': "The join table for exercises and muscles."}

    # Fields
    __tablename__ = "exercise_muscles"
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    muscle_id = db.Column(db.Integer, db.ForeignKey("muscle_library.id", ondelete='CASCADE'), primary_key=True)

    # Relationships
    exercises = db.relationship("Exercise_Library", back_populates = "muscles")
    muscles = db.relationship("Muscle_Library", back_populates = "exercises")
    
    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercises.name,
            "muscle_id": self.muscle_id,
            "muscle_name": self.muscles.name
        }





