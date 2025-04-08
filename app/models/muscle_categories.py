from app import db

# The components that exist for phase components.
class Muscle_Categories(db.Model):
    __table_args__ = {
        'comment': "The join table for the different muscle groups that exist."
    }
    # Fields
    __tablename__ = "muscle_categories"
    id = db.Column(db.Integer, primary_key=True)
    muscle_id = db.Column(db.Integer, db.ForeignKey("muscle_library.id", ondelete='CASCADE'), nullable=False)
    muscle_group_id = db.Column(db.Integer, db.ForeignKey("muscle_group_library.id", ondelete='CASCADE'), nullable=False)
    body_region_id = db.Column(db.Integer, db.ForeignKey("body_region_library.id", ondelete='CASCADE'), nullable=False)
    bodypart_id = db.Column(db.Integer, db.ForeignKey("bodypart_library.id", ondelete='CASCADE'), nullable=False)

    # Relationships
    muscles = db.relationship("Muscle_Library", back_populates="categories")
    muscle_groups = db.relationship("Muscle_Group_Library", back_populates="categories")
    body_regions = db.relationship("Body_Region_Library", back_populates="categories")
    bodyparts = db.relationship("Bodypart_Library", back_populates="categories")

    def to_dict(self):
        return {
            "id": self.id, 
            "muscle_id": self.muscle_id, 
            "muscle_name": self.muscles.name, 
            "muscle_group_id": self.muscle_group_id, 
            "muscle_group_name": self.muscle_groups.name, 
            "body_region_id": self.body_region_id, 
            "body_region_name": self.body_regions.name, 
            "bodypart_id": self.bodypart_id, 
            "bodypart_name": self.bodyparts.name
        }