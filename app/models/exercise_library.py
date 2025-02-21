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
    
    movement_type = db.Column(
        db.String(50), 
        nullable=False, 
        comment='E.g., Compound, Isolation')
    
    primary_muscle_group = db.Column(
        db.String(50), 
        nullable=False, 
        comment='E.g., Quadriceps, Chest')
    
    tempo = db.Column(
        db.String(50), 
        nullable=False, 
        comment='E.g., 2-0-2, 3-1-2')
    
    tracking = db.Column(
        db.String(50), 
        nullable=False, 
        comment='E.g., {"reps": 10, "time": 30, "weight": 50}')
    
    # Relationships
    equipment = db.relationship(
        "Exercise_Equipment",
        back_populates = "exercises",
        cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "movement_type": self.movement_type,
            "primary_muscle_group": self.primary_muscle_group,
            "tempo": self.tempo,
            "tracking": self.tracking,
        }
    