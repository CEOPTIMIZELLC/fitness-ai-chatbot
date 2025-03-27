from app import db

# The components that exist.
class Phase_Component_Library(db.Model):
    __table_args__ = {
        'comment': "The library of phase components that exists."
    }
    # Fields
    __tablename__ = "phase_component_library"
    id = db.Column(db.Integer, primary_key=True)
    phase_id = db.Column(db.Integer, db.ForeignKey("phase_library.id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("component_library.id"), nullable=False)
    subcomponent_id = db.Column(db.Integer, db.ForeignKey("subcomponent_library.id"), nullable=False)

    name = db.Column(
        db.String(50),
        nullable=False,
        comment='The name of the phase and subcomponent combination.')

    reps_min = db.Column(
        db.Integer, 
        nullable=False,
        comment='The minimum number of repetitions for a single exercise in the phase subcomponent.')
    reps_max = db.Column(
        db.Integer, 
        nullable=False,
        comment='The maximum number of repetitions for a single exercise in the phase subcomponent.')

    sets_min = db.Column(
        db.Integer, 
        nullable=False,
        comment='The minimum number of sets of repetitions for a single exercise in the phase subcomponent.')
    sets_max = db.Column(
        db.Integer, 
        nullable=False,
        comment='The maximum number of sets of repetitions for a single exercise in the phase subcomponent.')

    tempo = db.Column(
        db.String(50),
        nullable=False,
        comment='The tempo for every exercise in the phase subcomponent.')

    seconds_per_exercise = db.Column(
        db.Integer,
        default=3, 
        nullable=False,
        comment='The number of seconds a single exercise in the phase subcomponent.')

    intensity_min = db.Column(
        db.Integer, 
        comment='The minimum amount of intensity for a single exercise in the phase subcomponent.')
    intensity_max = db.Column(
        db.Integer, 
        comment='The maximum amount of intensity for a single exercise in the phase subcomponent.')

    rest_min = db.Column(
        db.Integer, 
        nullable=False,
        comment='The minimum amount of time to rest for a single exercise in the phase subcomponent.')
    rest_max = db.Column(
        db.Integer, 
        nullable=False,
        comment='The maximum amount of time to rest for a single exercise in the phase subcomponent.')

    required_every_workout = db.Column(
        db.Boolean,
        nullable=False, 
        comment='Whether or not the phase component is required for every workout in the microcycle.')

    required_within_microcycle = db.Column(
        db.String(50),
        nullable=False, 
        comment='Whether or not the phase component is required for every microcycle.')

    frequency_per_microcycle_min = db.Column(
        db.Integer, 
        comment='The minimum number of times the phase component may occur in a microcycle if included.')
    frequency_per_microcycle_max = db.Column(
        db.Integer, 
        comment='The maximum number of times the phase component may occur in a microcycle if included.')

    exercises_per_bodypart_workout_min = db.Column(
        db.Integer, 
        comment='The minimum number of exercises per bodypart included for a single phase component.')
    exercises_per_bodypart_workout_max = db.Column(
        db.Integer, 
        comment='The maximum number of exercises per bodypart included for a single phase component.')

    exercise_selection_note = db.Column(
        db.String(255),
        comment='')

    # Relationships
    phases = db.relationship(
        "Phase_Library",
        back_populates = "phase_components")

    components = db.relationship(
        "Component_Library",
        back_populates = "phase_components")

    subcomponents = db.relationship(
        "Subcomponent_Library",
        back_populates = "phase_components")
    
    user_exercises = db.relationship(
        "User_Exercises",
        back_populates = "phase_components",
        cascade="all, delete-orphan")

    workout_components = db.relationship(
        "User_Workout_Components",
        back_populates = "phase_components",
        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "phase_id": self.phase_id,
            "phase_name": self.phases.name,
            "component_id": self.component_id,
            "component_name": self.components.name,
            "subcomponent_id": self.subcomponent_id,
            "subcomponent_name": self.subcomponents.name,
            "name": self.name,
            "reps_min": self.reps_min,
            "reps_max": self.reps_max,
            "sets_min": self.sets_min,
            "sets_max": self.sets_max,
            "tempo": self.tempo,
            "seconds_per_exercise": self.seconds_per_exercise,
            "intensity_min": self.intensity_min,
            "intensity_max": self.intensity_max,
            "rest_min": self.rest_min,
            "rest_max": self.rest_max,
            "required_every_workout": self.required_every_workout,
            "required_within_microcycle": self.required_within_microcycle,
            "frequency_per_microcycle_min": self.frequency_per_microcycle_min,
            "frequency_per_microcycle_max": self.frequency_per_microcycle_max,
            "exercises_per_bodypart_workout_min": self.exercises_per_bodypart_workout_min,
            "exercises_per_bodypart_workout_max": self.exercises_per_bodypart_workout_max,
            "exercise_selection_note": self.exercise_selection_note
        }