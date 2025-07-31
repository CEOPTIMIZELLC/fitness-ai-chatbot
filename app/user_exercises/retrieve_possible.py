from app.models import (
    User_Equipment, 
    User_Exercises, 
    Exercise_Library, 
    Exercise_Supportive_Equipment, 
    Exercise_Assistive_Equipment, 
    Exercise_Weighted_Equipment, 
    Exercise_Marking_Equipment, 
    Exercise_Other_Equipment)

from app import db

# Retrieve all exercises that the user is able to perform.
def user_possible_exercises(user_id):
    user_exercises = (
        db.session.query(User_Exercises)
        .filter(User_Exercises.user_id == user_id)
        .order_by(User_Exercises.exercise_id.asc())
        .distinct()
        .all()
    )

    # Only include exercise that the user have all of the equipment for
    available_exercises = []
    for user_exercise in user_exercises:
        if user_exercise.has_all_equipment:
            available_exercises.append(user_exercise)
    return available_exercises

def user_possible_exercises_with_user_exercise_info(user_id):
    user_exercises = (
        db.session.query(Exercise_Library, User_Exercises)
        .join(User_Exercises, Exercise_Library.id == User_Exercises.exercise_id)
        .filter(User_Exercises.user_id == user_id)
        .order_by(Exercise_Library.id.asc())
        .distinct()
        .all()
    )

    available_exercises = []
    for user_exercise in user_exercises:
        if user_exercise[1].has_all_equipment:
            available_exercises.append(user_exercise)
    return available_exercises

#### These methods are more efficient, though I am still struggling to compare the count of the equipment ids to the quantity required. I will look more into this.
# Retrieve all exercises that the user is able to perform.
def user_available_exercises(user_id):
    user_equipment = (
        db.session.query(User_Equipment.equipment_id)
        .filter(User_Equipment.user_id == user_id)
        .scalar_subquery()
    )

    # Main query to get exercises where either:
    # 1. The exercise requires no equipment at all, or
    # 2. The user has all required equipment for the exercise
    available_exercises = (
        db.session.query(Exercise_Library)
        .outerjoin(Exercise_Supportive_Equipment)
        .outerjoin(Exercise_Assistive_Equipment)
        .outerjoin(Exercise_Weighted_Equipment)
        .outerjoin(Exercise_Marking_Equipment)
        .outerjoin(Exercise_Other_Equipment)
        .filter(
            # Either no equipment is required (all equipment relationships are NULL)
            ((Exercise_Supportive_Equipment.exercise_id.is_(None)) &
             (Exercise_Assistive_Equipment.exercise_id.is_(None)) &
             (Exercise_Weighted_Equipment.exercise_id.is_(None)) &
             (Exercise_Marking_Equipment.exercise_id.is_(None)) &
             (Exercise_Other_Equipment.exercise_id.is_(None)))
            |
            # Or all required equipment is owned by the user
            ((Exercise_Supportive_Equipment.equipment_id.in_(user_equipment) | 
              Exercise_Supportive_Equipment.equipment_id.is_(None)) &
             (Exercise_Assistive_Equipment.equipment_id.in_(user_equipment) | 
              Exercise_Assistive_Equipment.equipment_id.is_(None)) &
             (Exercise_Weighted_Equipment.equipment_id.in_(user_equipment) | 
              Exercise_Weighted_Equipment.equipment_id.is_(None)) &
             (Exercise_Marking_Equipment.equipment_id.in_(user_equipment) | 
              Exercise_Marking_Equipment.equipment_id.is_(None)) &
             (Exercise_Other_Equipment.equipment_id.in_(user_equipment) | 
              Exercise_Other_Equipment.equipment_id.is_(None)))
        )
        .order_by(Exercise_Library.id.asc())
        .distinct()
        .all()
    )
    return available_exercises