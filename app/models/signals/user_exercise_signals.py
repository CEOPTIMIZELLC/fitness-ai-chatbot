from app.models import Users, Exercise_Library, User_Exercises
from sqlalchemy import event

from sqlalchemy.orm import Session

# When a new user is added, create User_Exercises for all exercises
@event.listens_for(Users, 'after_insert')
def add_user_exercises(mapper, connection, target):
    session = Session(bind=connection)
    exercises = session.query(Exercise_Library).all()

    for exercise in exercises:
        one_rep_max = 10 if exercise.is_weighted else 0
        one_rep_load = 10 if exercise.is_weighted else 0
        session.add(User_Exercises(user_id=target.id, exercise_id=exercise.id, one_rep_max=one_rep_max, one_rep_load=one_rep_load))
    
    session.commit()
    session.close()

# When a new exercise is added, create User_Exercises for all users
@event.listens_for(Exercise_Library, 'after_insert')
def add_exercise_for_users(mapper, connection, target):
    session = Session(bind=connection)
    users = session.query(Users).all()

    one_rep_max = 10 if target.is_weighted else 0
    one_rep_load = 10 if target.is_weighted else 0
    for user in users:
        session.add(User_Exercises(user_id=user.id, exercise_id=target.id, one_rep_max=one_rep_max, one_rep_load=one_rep_load))

    session.commit()
    session.close()
