from app.models import Exercise_Library
exercises = [
    Exercise_Library(name="bench press", movement_type="compound", primary_muscle_group="chest", tempo="3-1-2", tracking='{"reps": 10, "time": 30, "weight": 50}'),
    Exercise_Library(name="bicep curl", movement_type="isolation", primary_muscle_group="biceps", tempo="3-0-1-0", tracking='{"reps": 10, "time": 30, "weight": 50}'),
    Exercise_Library(name="jogging", movement_type="isolation", primary_muscle_group="legs", tempo="3-0-1-0", tracking='{"reps": 10, "time": 30, "weight": 50}')
]