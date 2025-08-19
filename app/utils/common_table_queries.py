from datetime import date
from tqdm import tqdm
from sqlalchemy.orm import joinedload, selectinload

from app.models import (
    Goal_Library, 
    Users, 
    User_Macrocycles, 
    User_Mesocycles, 
    User_Microcycles, 
    User_Workout_Days, 
    User_Equipment, 
    User_Exercises, 
    User_Weekday_Availability, 
    Exercise_Component_Phases, 
    Exercise_Library, 
    Exercise_Supportive_Equipment, 
    Exercise_Assistive_Equipment, 
    Exercise_Weighted_Equipment, 
    Exercise_Marking_Equipment, 
    Exercise_Other_Equipment, 
    Weekday_Library)

from app import db


# Retrieve the latest, currently active workday for a user.
def current_weekday_availability(user_id):
    # Get the weekday as an integer (0 for Monday, 6 for Sunday)
    today = date.today().weekday()
    active_weekday_availability = (
        User_Weekday_Availability.query
        .filter(
            User_Weekday_Availability.user_id == user_id,
            User_Weekday_Availability.weekday_id == today)
        .first())
    return active_weekday_availability

# Retrieve the latest, currently active macrocycle for a user.
def current_macrocycle(user_id):
    today = date.today()
    active_macrocycle = (
        User_Macrocycles.query
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Macrocycles.start_date <= today, 
            User_Macrocycles.end_date >= today)
        .order_by(User_Macrocycles.id.desc())
        .first())
    return active_macrocycle

# Retrieve the latest, currently active mesocycle for a user.
def current_mesocycle(user_id):
    today = date.today()
    active_mesocycle = (
        User_Mesocycles.query
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Mesocycles.start_date <= today, 
            User_Mesocycles.end_date >= today)
        .order_by(User_Mesocycles.id.desc())
        .first())
    return active_mesocycle

# Retrieve the latest, currently active microcycle for a user.
def current_microcycle(user_id):
    today = date.today()
    active_microcycle = (
        User_Microcycles.query
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Microcycles.start_date <= today, 
            User_Microcycles.end_date >= today)
        .order_by(User_Microcycles.id.desc())
        .first())
    return active_microcycle

# Retrieve the latest, currently active workday for a user.
def current_workout_day(user_id):
    today = date.today()
    active_workout_day = (
        User_Workout_Days.query
        .join(User_Microcycles)
        .join(User_Mesocycles)
        .join(User_Macrocycles)
        .filter(
            User_Macrocycles.user_id == user_id,
            User_Workout_Days.date == today)
        .order_by(User_Workout_Days.id.desc())
        .first())
    return active_workout_day

# Check if an exercise has all of the equipment required.
def check_for_all_equipment(ex):
    return (
        ex.has_supportive_equipment[0] and 
        ex.has_assistive_equipment[0] and 
        ex.has_weighted_equipment[0] and 
        ex.has_marking_equipment[0] and 
        ex.has_other_equipment[0]
    )

# Retrieve all exercises that the user is able to perform.
def user_possible_exercises(user_id):
    user_exercises = (
        db.session.query(User_Exercises)
        .filter(User_Exercises.user_id == user_id)
        .order_by(User_Exercises.exercise_id.asc())
        .distinct()
        .all()
    )

    available_exercises = []
    for user_exercise in user_exercises:
        if check_for_all_equipment(user_exercise):
            available_exercises.append(user_exercise)
    return available_exercises

# Retrieve all exercises that the user is able to perform with the necessary information about it.
def user_possible_exercises_with_user_exercise_info(user_id):
    user_exercises = (
        db.session.query(Exercise_Library, User_Exercises)
        .join(User_Exercises, Exercise_Library.id == User_Exercises.exercise_id)
        .filter(User_Exercises.user_id == user_id)
        .order_by(Exercise_Library.id.asc())
        .options(
            # user -> their equipment
            joinedload(User_Exercises.users).selectinload(Users.equipment),

            # exercise -> each equipment bucket
            joinedload(User_Exercises.exercises).selectinload(Exercise_Library.supportive_equipment),
            joinedload(User_Exercises.exercises).selectinload(Exercise_Library.assistive_equipment),
            joinedload(User_Exercises.exercises).selectinload(Exercise_Library.weighted_equipment),
            joinedload(User_Exercises.exercises).selectinload(Exercise_Library.marking_equipment),
            joinedload(User_Exercises.exercises).selectinload(Exercise_Library.other_equipment),
        )
        .all()
    )

    # Access each has_* once; or better, call your single combined checker if you added it.
    available_exercises = []
    for user_exercise in tqdm(user_exercises, total=len(user_exercises), desc="Creating available exercise information list"):
        if check_for_all_equipment(user_exercise[1]):
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