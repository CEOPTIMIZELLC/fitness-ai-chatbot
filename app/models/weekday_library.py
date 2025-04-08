from app import db

# The days of the week.
class Weekday_Library(db.Model):
    __table_args__ = {
        'comment': "The library of week days that exist."
    }
    # Fields
    __tablename__ = "weekday_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Relationships
    availability = db.relationship(
        "User_Weekday_Availability", 
        back_populates="weekdays", 
        cascade="all, delete-orphan")

    workout_days = db.relationship(
        "User_Workout_Days", 
        back_populates="weekdays", 
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name
        }