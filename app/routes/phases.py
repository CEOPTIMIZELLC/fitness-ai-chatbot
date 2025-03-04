from flask import request, jsonify, Blueprint

from app.models import Phase_Library

bp = Blueprint('phases', __name__)

# ----------------------------------------- Phases -----------------------------------------

# Retrieve phases
@bp.route('/', methods=['GET'])
def get_phase_list():
    phases = Phase_Library.query.all()
    result = []
    for phase in phases:
        result.append(phase.to_dict())
    return jsonify({"status": "success", "phases": result}), 200

# Show phases based on id.
@bp.route('/<phase_id>', methods=['GET'])
def read_phase(phase_id):
    phase = Phase_Library.query.filter_by(id=phase_id).first()
    if not phase:
        return jsonify({"status": "error", "message": "Phase " + phase_id + " not found."}), 404
    return jsonify(phase.to_dict()), 200
