from app import db

# The exercises that exist.
class Exercise_Library(db.Model):
    # Fields
    __table_args__ = {
        'comment': "The library of exercises that exists."
    }
    __tablename__ = "exercise_library"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False, 
        comment='E.g., Squat, Dead Bug Exercise')

    base_strain = db.Column(
        db.Integer, 
        nullable=False,
        comment='The base strain for the exercise.')

    technical_difficulty = db.Column(
        db.Integer, 
        nullable=False,
        comment='The difficulty to perform the exercise.')
    
    tags = db.Column(db.String(50))
    sides = db.Column(db.String(50))
    body_position = db.Column(db.String(50))
    option_for_added_weight = db.Column(db.String(50))
    proprioceptive_progressions = db.Column(db.String(50))
    
    # Relationships
    '''equipment = db.relationship(
        "Exercise_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")'''

    muscles = db.relationship(
        "Exercise_Muscles",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    muscle_groups = db.relationship(
        "Exercise_Muscle_Groups",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    body_regions = db.relationship(
        "Exercise_Body_Regions",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    bodyparts = db.relationship(
        "Exercise_Bodyparts",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    supportive_equipment = db.relationship(
        "Exercise_Supportive_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    assistive_equipment = db.relationship(
        "Exercise_Assistive_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    weighted_equipment = db.relationship(
        "Exercise_Weighted_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    marking_equipment = db.relationship(
        "Exercise_Marking_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    other_equipment = db.relationship(
        "Exercise_Other_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "base_strain": self.base_strain,
            "technical_difficulty": self.technical_difficulty,
            "tags": self.tags,
            "sides": self.sides,
            "body_position": self.body_position,
            "option_for_added_weight": self.option_for_added_weight,
            "proprioceptive_progressions": self.proprioceptive_progressions,
        }
    