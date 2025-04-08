from app import db

class Muscle_Library(db.Model):
    __table_args__ = {
        'comment': "The library of muscles."
    }
    # Fields
    __tablename__ = "muscle_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False)

    # Relationships
    categories = db.relationship(
        "Muscle_Categories", 
        back_populates="muscles", 
        cascade="all, delete-orphan")

    exercises = db.relationship(
        "Exercise_Muscles", 
        back_populates="muscles", 
        cascade="all, delete-orphan")


    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }