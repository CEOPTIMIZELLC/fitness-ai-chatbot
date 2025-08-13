from datetime import datetime, date
import math
from app import db
from config import ExercisePerformanceDecayConfig as PerformanceConfig
from config import ExerciseOneRepMaxDecayConfig as OneRepMaxConfig
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import BaseModel
from app.models.mixins import TableNameMixin
from collections import defaultdict, Counter

# Linear Decay
def linear_value_change(original_value, days_since, decay_rate=-0.01):
    performance_change = (decay_rate * days_since)
    decayed_value = original_value + performance_change
    return decayed_value

# Exponential Decay
def exponential_value_change(original_value, days_since, decay_rate=-0.01):
    performance_change = math.exp(decay_rate * days_since)
    decayed_value = original_value * performance_change
    return decayed_value

# Retrieve the Decayed version of the original value.
def decayed_value(original_value, days_since, exercise_metric_config):
    grace_period = exercise_metric_config.grace_period
    decay_rate = -abs(exercise_metric_config.decay_rate)
    exponential_decay = exercise_metric_config.exponential_decay

    # Wait for the grace period to end before altering the original value.
    if days_since <= grace_period:
        return original_value

    # Only use period of time after the grace period.
    effective_days = days_since - grace_period

    # Perform either exponential or linear rate of decay depending on configuration.
    if exponential_decay:
        return exponential_value_change(original_value, effective_days, decay_rate)
    return linear_value_change(original_value, effective_days, decay_rate)

class User_Exercises(db.Model, TableNameMixin):
    """Exercise available to a user during a training period."""
    __table_args__ = {'comment': "The exercises that a user has performed."}

    # Fields
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise_library.id", ondelete='CASCADE'), primary_key=True)
    one_rep_max = db.Column(db.Integer, nullable=False, default=10, comment='The maximum weight that the user can lift for one repetition of the exercise.')
    one_rep_load = db.Column(db.Integer, nullable=False, default=10, comment='The weight that the user can lift for one repetition of the exercise.')
    volume = db.Column(db.Integer, nullable=False, default=0, comment='sets * reps * load')
    density = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='working duration / duration')
    intensity = db.Column(db.Integer, nullable=False, default=100, comment='The intensity of the exercise in comparison to the their one rep max.')
    performance = db.Column(db.Numeric(10, 2), nullable=False, default=0, comment='density * volume')
    duration = db.Column(db.Integer, nullable=False, default=0, comment='The duration of the exercise.')
    working_duration = db.Column(db.Integer, nullable=False, default=0, comment='The working duration of the exercise.')
    last_performed = db.Column(db.Date, nullable=False, default=db.func.current_timestamp(), comment='Date that the exercise was last performed.')

    # Relationships
    users = db.relationship("Users", back_populates="exercises")
    exercises = db.relationship("Exercise_Library", back_populates="users")

    @hybrid_property
    def days_since(self):
        days_since = (date.today() - self.last_performed).days
        return days_since

    @hybrid_property
    def one_rep_max_decayed(self):
        if not self.exercises.is_weighted: 
            return 0
        decayed_one_rep_max = decayed_value(
            original_value = self.one_rep_max, 
            days_since = self.days_since, 
            exercise_metric_config = OneRepMaxConfig)

        one_rep_max = int(decayed_one_rep_max)

        if one_rep_max < 10:
            return 10
        return one_rep_max

    @hybrid_property
    def performance_decayed(self):
        decayed_performance = decayed_value(
            original_value = float(self.performance), 
            days_since = self.days_since, 
            exercise_metric_config = PerformanceConfig)

        return round(decayed_performance, 2)

    def _user_equipment_map(self):
        m = defaultdict(list)
        for eq in self.users.equipment:
            m[eq.equipment_id].append(eq.measurement)
        return m

    def has_equipment(self, required_equipment, _user_map=None):
        if not required_equipment:
            return True, {}

        # Group user equipment by equipment_id and count measurements
        user_equipment = _user_map or self._user_equipment_map()
        for eq in self.users.equipment:
            user_equipment[eq.equipment_id].append(eq.measurement)

        # Group required equipment by relationship
        equipment_by_relationship = defaultdict(list)
        for eq in required_equipment:
            relationship = eq.equipment_relationship or 'None'
            equipment_by_relationship[relationship].append({
                'equipment_id': eq.equipment_id,
                'quantity': eq.quantity or 1
            })

        valid_measurements = defaultdict(list)

        # Evaluate each relationship group
        for relationship, equipment_list in equipment_by_relationship.items():
            if relationship.lower() == 'or':
                # Must satisfy AT LEAST ONE requirement group
                satisfied = False
                for eq in equipment_list:
                    available = user_equipment.get(eq['equipment_id'], [])
                    counter = Counter(available)
                    possible = [m for m, count in counter.items() if count >= eq['quantity']]
                    if possible:
                        satisfied = True
                        valid_measurements[eq['equipment_id']].extend(sorted(possible))
                if not satisfied:
                    return False, {}
            else:
                # Must satisfy ALL requirements
                for eq in equipment_list:
                    available = user_equipment.get(eq['equipment_id'], [])
                    counter = Counter(available)
                    possible = [m for m, count in counter.items() if count >= eq['quantity']]
                    if not possible:
                        return False, {}
                    valid_measurements[eq['equipment_id']].extend(sorted(possible))

        # Remove duplicates in measurement lists
        for eq_id in valid_measurements:
            valid_measurements[eq_id] = sorted(set(valid_measurements[eq_id]))

        return True, dict(valid_measurements)

    def has_all_equipment_fast(self):
        user_map = self._user_equipment_map()
        checks = (
            self.has_equipment(self.exercises.supportive_equipment, user_map)[0],
            self.has_equipment(self.exercises.assistive_equipment, user_map)[0],
            self.has_equipment(self.exercises.weighted_equipment, user_map)[0],
            self.has_equipment(self.exercises.marking_equipment, user_map)[0],
            self.has_equipment(self.exercises.other_equipment, user_map)[0],
        )
        return all(checks)

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

    def to_dict(self):
        return {
            "user_id": self.user_id, 
            "exercise_id": self.exercise_id, 
            "exercise_name": self.exercises.name,
            "is_weighted": self.exercises.is_weighted,
            "days_since": self.days_since,
            "last_performed": self.last_performed,
            "one_rep_max": self.one_rep_max,
            "one_rep_max_decayed": self.one_rep_max_decayed,
            "one_rep_load": self.one_rep_load,
            "volume": self.volume,
            "density": self.density,
            "intensity": self.intensity,
            "performance": self.performance,
            "performance_decayed": self.performance_decayed, 
            "duration": self.duration,
            "working_duration": self.working_duration,
            "has_supportive_equipment": self.has_supportive_equipment,
            "has_assistive_equipment": self.has_assistive_equipment,
            "has_weighted_equipment": self.has_weighted_equipment,
            "has_marking_equipment": self.has_marking_equipment,
            "has_other_equipment": self.has_other_equipment,
        }
