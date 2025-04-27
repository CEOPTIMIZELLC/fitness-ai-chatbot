from app import db
from app.models.mixins import TableNameMixin

# The phases that exist.
class User_Weekday_Availability(db.Model, TableNameMixin):
    __table_args__ = {'comment': "The phases that a mesocycle may be tagged with."}
    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    weekday_id = db.Column(db.Integer, db.ForeignKey("weekday_library.id", ondelete='CASCADE'), primary_key=True)
    availability = db.Column(
        db.Interval, 
        nullable=False, 
        comment='The amount of time the user is allowed on this day.')

    # Relationships
    users = db.relationship("Users", back_populates="availability")
    weekdays = db.relationship("Weekday_Library", back_populates="availability")

    def to_dict(self):
        return {
            "user_id": self.user_id, 
            "weekday_id": self.weekday_id, 
            "weekday_name": self.weekdays.name, 
            "availability": self.availability.total_seconds()
        }