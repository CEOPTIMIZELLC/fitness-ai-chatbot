from tqdm import tqdm
from app import db
from app.models import Goal_Library, Goal_Phase_Requirements, Phase_Library

# Retrieve the phase types and their corresponding constraints for a goal.
def retrieve_phase_constraints_for_goal(goal_id):
    # Retrieve all possible phases that can be selected.
    possible_phases = (
        db.session.query(
            Phase_Library.id,
            Phase_Library.name,
            Phase_Library.phase_duration_minimum_in_weeks,
            Phase_Library.phase_duration_maximum_in_weeks,
            Goal_Phase_Requirements.required_phase,
            Goal_Phase_Requirements.is_goal_phase,
        )
        .join(Goal_Phase_Requirements, Goal_Phase_Requirements.phase_id == Phase_Library.id)
        .join(Goal_Library, Goal_Library.id == Goal_Phase_Requirements.goal_id)
        .filter(Goal_Library.id == goal_id)
        .order_by(Phase_Library.id.asc())
        .all()
    )
    return possible_phases

dummy_phase = {
    "id": 0,
    "name": "Inactive",
    "element_minimum": 0,
    "element_maximum": 0,
    "required_phase": False,
    "is_goal_phase": False,
}

def phase_dict(possible_phase):
    """Format the phase component data."""
    return {
        "id": possible_phase.id,
        "name": possible_phase.name.lower(),
        "element_minimum": possible_phase.phase_duration_minimum_in_weeks.days // 7,
        "element_maximum": possible_phase.phase_duration_maximum_in_weeks.days // 7,
        "required_phase": True if possible_phase.required_phase == "required" else False,
        #"required_phase": possible_phase.required_phase,
        "is_goal_phase": possible_phase.is_goal_phase,
    }

def construct_phases_list(possible_phases):
    # Convert the phases to a list form.
    possible_phases_list = [dummy_phase]
    for possible_phase in tqdm(possible_phases, total=len(possible_phases), desc="Creating phase list from entries"):
        possible_phases_list.append(phase_dict(possible_phase))
    return possible_phases_list

# Retrieve all possible phases that can be selected and convert them into a list form.
def Main(goal_id):
    possible_phases = retrieve_phase_constraints_for_goal(goal_id)
    return construct_phases_list(possible_phases)