from app.models import Goal_Phase_Requirements
#
goal_phase_requirements = [
    Goal_Phase_Requirements(goal_id=1, phase_id=1, required_phase="required", is_goal_phase=True),
    Goal_Phase_Requirements(goal_id=1, phase_id=2, required_phase="required", is_goal_phase=True),
    Goal_Phase_Requirements(goal_id=1, phase_id=3, required_phase="optional", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=1, phase_id=4, required_phase="unlikely", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=1, phase_id=5, required_phase="unlikely", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=2, phase_id=1, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=2, phase_id=2, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=2, phase_id=3, required_phase="required", is_goal_phase=True),
    Goal_Phase_Requirements(goal_id=2, phase_id=4, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=2, phase_id=5, required_phase="unlikely", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=3, phase_id=1, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=3, phase_id=2, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=3, phase_id=3, required_phase="unlikely", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=3, phase_id=4, required_phase="required", is_goal_phase=False),
    Goal_Phase_Requirements(goal_id=3, phase_id=5, required_phase="required", is_goal_phase=True),

]