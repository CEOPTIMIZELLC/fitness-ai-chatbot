from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.mixins import LibraryMixin

# The exercises that exist.
class Exercise_Library(db.Model, LibraryMixin):
    # Fields
    __table_args__ = {
        'comment': "The library of exercises that exists."
    }
    __tablename__ = "exercise_library"

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
    component_phases = db.relationship(
        "Exercise_Component_Phases", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    muscles = db.relationship(
        "Exercise_Muscles", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    muscle_groups = db.relationship(
        "Exercise_Muscle_Groups", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    bodyparts = db.relationship(
        "Exercise_Bodyparts", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    body_regions = db.relationship(
        "Exercise_Body_Regions", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    supportive_equipment = db.relationship(
        "Exercise_Supportive_Equipment", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    assistive_equipment = db.relationship(
        "Exercise_Assistive_Equipment", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    weighted_equipment = db.relationship(
        "Exercise_Weighted_Equipment", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    marking_equipment = db.relationship(
        "Exercise_Marking_Equipment", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    other_equipment = db.relationship(
        "Exercise_Other_Equipment", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    user_exercises = db.relationship(
        "User_Exercises", 
        back_populates="exercises", 
        cascade="all, delete-orphan")

    @hybrid_property
    def all_muscle_ids(self):
        # Direct muscles
        direct_ids = {i.muscle_id for i in self.muscles}
        
        # Muscles from muscle groups, bodyparts, and body regions
        category_ids = (
            {mc.muscle_id 
             for mg in self.muscle_groups 
             for mc in mg.muscle_groups.categories} | 
            {mc.muscle_id 
             for bp in self.bodyparts 
             for mc in bp.bodyparts.categories} | 
            {mc.muscle_id 
             for br in self.body_regions 
             for mc in br.body_regions.categories})
        
        return list(set(direct_ids | category_ids))

    @hybrid_property
    def all_muscle_group_ids(self):
        # Direct muscle groups
        direct_ids = {i.muscle_group_id for i in self.muscle_groups}

        # Muscle groups from muscles, bodyparts, and body regions
        category_ids = (
            {mc.muscle_group_id 
             for m in self.muscles 
             for mc in m.muscles.categories} | 
            {mc.muscle_group_id 
             for bp in self.bodyparts 
             for mc in bp.bodyparts.categories} | 
            {mc.muscle_group_id 
             for br in self.body_regions 
             for mc in br.body_regions.categories})
        
        return list(set(direct_ids | category_ids))

    @hybrid_property
    def all_bodypart_ids(self):
        # Direct bodyparts
        direct_ids = {i.bodypart_id for i in self.bodyparts}
        
        # Bodyparts from muscles, muscle groups, and body regions
        category_ids = (
            {mc.bodypart_id 
             for m in self.muscles 
             for mc in m.muscles.categories} | 
            {mc.bodypart_id 
             for mg in self.muscle_groups 
             for mc in mg.muscle_groups.categories} | 
            {mc.bodypart_id 
             for br in self.body_regions 
             for mc in br.body_regions.categories})
        
        return list(set(direct_ids | category_ids))

    @hybrid_property
    def all_body_region_ids(self):
        # Direct body regions
        direct_ids = {i.body_region_id for i in self.body_regions}
        
        # Body regions from muscles, muscle groups, and bodyparts
        category_ids = (
            {mc.body_region_id 
             for m in self.muscles 
             for mc in m.muscles.categories} | 
            {mc.body_region_id 
             for mg in self.muscle_groups 
             for mc in mg.muscle_groups.categories} | 
            {mc.body_region_id 
             for bp in self.bodyparts 
             for mc in bp.bodyparts.categories})
        
        return list(set(direct_ids | category_ids))

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
            "muscle_ids": self.all_muscle_ids, 
            "muscle_group_ids": self.all_muscle_group_ids, 
            "bodypart_ids": self.all_bodypart_ids, 
            "body_region_ids": self.all_body_region_ids, 
        }
    
