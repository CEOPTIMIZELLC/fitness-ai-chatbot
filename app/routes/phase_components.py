from flask import request, jsonify, Blueprint

from app.models import Phase_Components, Phase_Components_Library, Phase_Subcomponents_Library

bp = Blueprint('phase_components', __name__)

# ----------------------------------------- Phase Components -----------------------------------------

# Retrieve all
@bp.route('/', methods=['GET'])
def get_phase_components_all():
    phase_components = Phase_Components.query.all()
    phase_components_result = []
    for phase_component in phase_components:
        phase_components_result.append(phase_component.to_dict())

    components = Phase_Components_Library.query.all()
    components_result = []
    for component in components:
        components_result.append(component.to_dict())

    subcomponents = Phase_Subcomponents_Library.query.all()
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
    phase_components = Phase_Components.query.all()
    result = []
    for phase_component in phase_components:
        result.append(phase_component.to_dict())
    return jsonify({"status": "success", "phase_components": result}), 200

# Show phase components based on id.
@bp.route('/phase_components/<phase_component_id>', methods=['GET'])
def read_phase_component(phase_component_id):
    phase_component = Phase_Components.query.filter_by(id=phase_component_id).first()
    if not phase_component:
        return jsonify({"status": "error", "message": "Phase Component " + phase_component_id + " not found."}), 404
    return jsonify(phase_component.to_dict()), 200


# Retrieve phase components
@bp.route('/components', methods=['GET'])
def get_components_list():
    components = Phase_Components_Library.query.all()
    result = []
    for component in components:
        result.append(component.to_dict())
    return jsonify({"status": "success", "components": result}), 200

# Show phase components based on id.
@bp.route('/components/<component_id>', methods=['GET'])
def read_component(component_id):
    component = Phase_Components_Library.query.filter_by(id=component_id).first()
    if not component:
        return jsonify({"status": "error", "message": "Phase Component " + component_id + " not found."}), 404
    return jsonify(component.to_dict()), 200


# Retrieve phase subcomponents
@bp.route('/subcomponents', methods=['GET'])
def get_subcomponents_list():
    subcomponents = Phase_Subcomponents_Library.query.all()
    result = []
    for subcomponent in subcomponents:
        result.append(subcomponent.to_dict())
    return jsonify({"status": "success", "subcomponents": result}), 200

# Show phase subcomponents based on id.
@bp.route('/subcomponents/<subcomponent_id>', methods=['GET'])
def read_subcomponent(subcomponent_id):
    subcomponent = Phase_Subcomponents_Library.query.filter_by(id=subcomponent_id).first()
    if not subcomponent:
        return jsonify({"status": "error", "message": "Phase Component " + subcomponent_id + " not found."}), 404
    return jsonify(subcomponent.to_dict()), 200
