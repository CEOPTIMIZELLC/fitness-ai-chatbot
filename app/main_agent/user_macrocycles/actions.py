from app import db
from app.models import Goal_Library, User_Macrocycles

# ----------------------------------------- User Macrocycles -----------------------------------------
# Retrieve possible goal types.
def retrieve_goal_types():
    goals = db.session.query(Goal_Library.id, Goal_Library.name).all()

    return [
        {
            "id": goal.id, 
            "name": goal.name.lower()
        } 
        for goal in goals
    ]

def new_macrocycle(user_id, goal_id, new_goal):
    new_macrocycle = User_Macrocycles(user_id=user_id, goal_id=goal_id, goal=new_goal)
    db.session.add(new_macrocycle)
    db.session.commit()
    return new_macrocycle

def alter_macrocycle(macrocycle_id, goal_id, new_goal):
    user_macrocycle = db.session.get(User_Macrocycles, macrocycle_id)
    user_macrocycle.goal = new_goal
    user_macrocycle.goal_id = goal_id
    db.session.commit()
    return user_macrocycle