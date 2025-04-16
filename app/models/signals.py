from app.models import Users, Exercise_Library, User_Exercises
from sqlalchemy.event import listens_for

@listens_for(Users, 'after_insert')
def connect_user_to_exercises(mapper, connection, user):
    # Get all existing exercises using the connection directly
    exercises = connection.execute(
        Exercise_Library.__table__.select()
    ).fetchall()
    
    # Prepare the values for bulk insert
    values = [
        {
            'user_id': user.id,
            'exercise_id': exercise.id,
            'one_rep_max': 10
        }
        for exercise in exercises
    ]
    
    if values:
        # Use the same connection to insert the records
        connection.execute(
            User_Exercises.__table__.insert(),
            values
        )

@listens_for(Exercise_Library, 'after_insert')
def connect_exercise_to_users(mapper, connection, exercise):
    # Get all existing users using the connection directly
    users = connection.execute(
        Users.__table__.select()
    ).fetchall()
    
    # Prepare the values for bulk insert
    values = [
        {
            'user_id': user.id,
            'exercise_id': exercise.id,
            'one_rep_max': 10
        }
        for user in users
    ]
    
    if values:
        # Use the same connection to insert the records
        connection.execute(
            User_Exercises.__table__.insert(),
            values
        )
