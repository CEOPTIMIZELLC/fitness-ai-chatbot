from flask import request, jsonify, Blueprint
from app import db
from app.models import Phase_Component_Library, Component_Library, Subcomponent_Library

bp = Blueprint('phase_components', __name__)

# ----------------------------------------- Phase Components -----------------------------------------

# Retrieve all
@bp.route('/', methods=['GET'])
def get_phase_components_all():
    phase_components = Phase_Component_Library.query.all()
    phase_components_result = []
    for phase_component in phase_components:
        phase_components_result.append(phase_component.to_dict())

    components = Component_Library.query.all()
    components_result = []
    for component in components:
        components_result.append(component.to_dict())

    subcomponents = Subcomponent_Library.query.all()
    subcomponents_result = []
    for subcomponent in subcomponents:
        subcomponents_result.append(subcomponent.to_dict())

    return jsonify(
        {"status": "success", 
         "phase_components": phase_components_result,
         "components": components_result,
         "subcomponents": subcomponents_result,
         }), 200


# Retrieve phase components
@bp.route('/phase_components', methods=['GET'])
def get_phase_components_list():
    phase_components = Phase_Component_Library.query.all()
    result = []
    for phase_component in phase_components:
        result.append(phase_component.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Show phase components based on id.
@bp.route('/phase_components/<phase_component_id>', methods=['GET'])
def read_phase_component(phase_component_id):
    phase_component = db.session.get(Phase_Component_Library, phase_component_id)
    if not phase_component:
        return jsonify({"status": "error", "message": "Phase Component " + phase_component_id + " not found."}), 404
    return jsonify({"status": "success", "phase_components": phase_component.to_dict()}), 200


# Retrieve phase components
@bp.route('/components', methods=['GET'])
def get_components_list():
    components = Component_Library.query.all()
    result = []
    for component in components:
        result.append(component.to_dict())
    return jsonify({"status": "success", "components": result}), 200

# Show phase components based on id.
@bp.route('/components/<component_id>', methods=['GET'])
def read_component(component_id):
    component = db.session.get(Component_Library, component_id)
    if not component:
        return jsonify({"status": "error", "message": "Phase Component " + component_id + " not found."}), 404
    return jsonify({"status": "success", "components": component.to_dict()}), 200


# Retrieve phase subcomponents
@bp.route('/subcomponents', methods=['GET'])
def get_subcomponents_list():
    subcomponents = Subcomponent_Library.query.all()
    result = []
    for subcomponent in subcomponents:
        result.append(subcomponent.to_dict())
    return jsonify({"status": "success", "subcomponents": result}), 200

# Show phase subcomponents based on id.
@bp.route('/subcomponents/<subcomponent_id>', methods=['GET'])
def read_subcomponent(subcomponent_id):
    subcomponent = db.session.get(Subcomponent_Library, subcomponent_id)
    if not subcomponent:
        return jsonify({"status": "error", "message": "Phase Component " + subcomponent_id + " not found."}), 404
    return jsonify({"status": "success", "subcomponents": subcomponent.to_dict()}), 200
