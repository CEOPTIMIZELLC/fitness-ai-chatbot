from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin

class User_Exercises(db.Model, TableNameMixin):
    """Exercise available to a user during a training period."""
    __table_args__ = {'comment': "The exercises that a user has performed."}

    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    one_rep_max = db.Column(db.Numeric(10, 2), nullable=False, default=10, comment='The maximum weight that the user can lift for one repetition of the exercise.')
    one_rep_load = db.Column(db.Numeric(10, 2), nullable=False, default=10, comment='The weight that the user can lift for one repetition of the exercise.')
    volume = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='sets * reps * load')
    density = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='working duration / duration')
    intensity = db.Column(db.Integer, nullable=False, default=100, comment='The intensity of the exercise in comparison to the their one rep max.')
    performance = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='density * volume')

    # Relationships
    users = db.relationship("Users", back_populates="exercises")
    exercises = db.relationship("Exercise_Library", back_populates="users")

    def has_equipment(self, required_equipment):
        # If no equipment is required, return True
        if not required_equipment:
            return True
        
        # Create a dictionary of user equipment with their quantities
        user_equipment = {}
        for eq in self.users.equipment:
            if eq.equipment_id not in user_equipment:
                user_equipment[eq.equipment_id] = 0
            user_equipment[eq.equipment_id] += 1
        
        # Group equipment by relationship
        equipment_by_relationship = {}
        for eq in required_equipment:
            relationship = eq.equipment_relationship or 'None'  # Default to 'None' if no relationship
            if relationship not in equipment_by_relationship:
                equipment_by_relationship[relationship] = []
            equipment_by_relationship[relationship].append({
                'equipment_id': eq.equipment_id,
                'quantity': eq.quantity or 1  # Default to 1 if quantity not specified
            })
        
        # Check each relationship group
        for relationship, equipment_list in equipment_by_relationship.items():
            if relationship in ['or', 'Or', 'OR']:
                # Must have AT LEAST ONE equipment in this group with sufficient quantity
                has_one = False
                for eq in equipment_list:
                    user_quantity = user_equipment.get(eq['equipment_id'], 0)
                    if user_quantity >= eq['quantity']:
                        has_one = True
                        break
                if not has_one:
                    return False
            else:
                # Must have ALL equipment in this group with sufficient quantities
                for eq in equipment_list:
                    user_quantity = user_equipment.get(eq['equipment_id'], 0)
                    if user_quantity < eq['quantity']:
                        return False

        return True

    @hybrid_property
    def has_supportive_equipment(self):
        return self.has_equipment(self.exercises.supportive_equipment)

    @hybrid_property
    def has_assistive_equipment(self):
        return self.has_equipment(self.exercises.assistive_equipment)

    @hybrid_property
    def has_weighted_equipment(self):
        return self.has_equipment(self.exercises.weighted_equipment)

    @hybrid_property
    def has_marking_equipment(self):
        return self.has_equipment(self.exercises.marking_equipment)

    @hybrid_property
    def has_other_equipment(self):
        return self.has_equipment(self.exercises.other_equipment)

    @hybrid_property
    def has_all_equipment(self):
        return (self.has_supportive_equipment 
                and self.has_assistive_equipment 
                and self.has_weighted_equipment 
                and self.has_marking_equipment 
                and self.has_other_equipment)

    def to_dict(self):
        return {
            "user_id": self.user_id, 
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name,
            "one_rep_max": self.one_rep_max,
            "one_rep_load": self.one_rep_load,
            "volume": self.volume,
            "density": self.density,
            "intensity": self.intensity,
            "performance": self.performance,
            "has_supportive_equipment": self.has_supportive_equipment,
            "has_assistive_equipment": self.has_assistive_equipment,
            "has_weighted_equipment": self.has_weighted_equipment,
            "has_marking_equipment": self.has_marking_equipment,
            "has_other_equipment": self.has_other_equipment,
            # "has_all_equipment": self.has_all_equipment,
        }
