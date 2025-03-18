from app import db

# The components that exist for phase components.
class Bodypart_Library(db.Model):
    __table_args__ = {
        'comment': "The library of components that exist for phase components."
    }
    # Fields
    __tablename__ = "bodypart_library"
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False)

    # Relationships
    phase_component_bodyparts = db.relationship(
        "Phase_Component_Bodyparts",
        back_populates = "bodyparts",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }