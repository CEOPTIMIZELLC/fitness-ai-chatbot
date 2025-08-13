from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin, NameMixin

# The exercises that exist.
class Exercise_Library(BaseModel, TableNameMixin, NameMixin):
    __table_args__ = {'comment': "The library of exercises that exists."}
    # Fields
    general_exercise_id = db.Column(db.Integer, db.ForeignKey("general_exercise_library.id", ondelete='CASCADE'), nullable=False)

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
    general_exercises = db.relationship("General_Exercise_Library", back_populates="exercises")

    component_phases = db.relationship(
        "Exercise_Component_Phases", 
        back_populates="exercises", 
        cascade="all, delete")

    muscles = db.relationship(
        "Exercise_Muscles", 
        back_populates="exercises", 
        cascade="all, delete")

    muscle_groups = db.relationship(
        "Exercise_Muscle_Groups", 
        back_populates="exercises", 
        cascade="all, delete")

    bodyparts = db.relationship(
        "Exercise_Bodyparts", 
        back_populates="exercises", 
        cascade="all, delete")

    body_regions = db.relationship(
        "Exercise_Body_Regions", 
        back_populates="exercises", 
        cascade="all, delete")

    supportive_equipment = db.relationship(
        "Exercise_Supportive_Equipment", 
        back_populates="exercises", 
        cascade="all, delete")

    assistive_equipment = db.relationship(
        "Exercise_Assistive_Equipment", 
        back_populates="exercises", 
        cascade="all, delete")

    weighted_equipment = db.relationship(
        "Exercise_Weighted_Equipment", 
        back_populates="exercises", 
        cascade="all, delete")

    marking_equipment = db.relationship(
        "Exercise_Marking_Equipment", 
        back_populates="exercises", 
        cascade="all, delete")

    other_equipment = db.relationship(
        "Exercise_Other_Equipment", 
        back_populates="exercises", 
        cascade="all, delete")

    user_workout_exercises = db.relationship(
        "User_Workout_Exercises", 
        back_populates="exercises", 
        cascade="all, delete")

    users = db.relationship(
        "User_Exercises", 
        back_populates="exercises", 
        cascade="all, delete")

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

    @hybrid_property
    def all_supportive_equipment(self):
        return [equipment.to_dict() for equipment in self.supportive_equipment]

    @hybrid_property
    def all_assistive_equipment(self):
        return [equipment.to_dict() for equipment in self.assistive_equipment]

    @hybrid_property
    def all_weighted_equipment(self):
        return [equipment.to_dict() for equipment in self.weighted_equipment]
    
    @hybrid_property
    def is_weighted(self):
        return len(self.weighted_equipment) > 0

    @hybrid_property
    def all_marking_equipment(self):
        return [equipment.to_dict() for equipment in self.marking_equipment]

    @hybrid_property
    def all_other_equipment(self):
        return [equipment.to_dict() for equipment in self.other_equipment]

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "general_exercise_id": self.general_exercise_id, 
            "general_exercise_name": self.general_exercises.name, 
            "base_strain": self.base_strain, 
            "technical_difficulty": self.technical_difficulty, 
            "tags": self.tags, 
            "sides": self.sides, 
            "body_position": self.body_position, 
            "option_for_added_weight": self.option_for_added_weight, 
            "is_weighted": self.is_weighted, 
            "proprioceptive_progressions": self.proprioceptive_progressions, 
        }