from flask import Blueprint, jsonify
from app.routes.blueprint_factories.libraries import create_library_crud_blueprint
from app.models import (
    Component_Library, 
    Equipment_Library, 
    General_Exercise_Library, 
    Exercise_Library, 
    Goal_Library, 
    Loading_System_Library, 
    Phase_Component_Library, 
    Phase_Library, 
    Subcomponent_Library
)

components_bp = create_library_crud_blueprint('components', '/components', Component_Library, 'components')
equipment_bp = create_library_crud_blueprint('equipment', '/equipment', Equipment_Library, 'equipment')
general_exercises_bp = create_library_crud_blueprint('general_exercises', '/general_exercises', General_Exercise_Library, 'general_exercises')
exercises_bp = create_library_crud_blueprint('exercises', '/exercises', Exercise_Library, 'exercises')
goals_bp = create_library_crud_blueprint('goals', '/goals', Goal_Library, 'goals')
loading_systems_bp = create_library_crud_blueprint('loading_systems', '/loading_systems', Loading_System_Library, 'loading_systems')
phase_components_bp = create_library_crud_blueprint('phase_components', '/phase_components', Phase_Component_Library, 'phase_components')
phases_bp = create_library_crud_blueprint('phases', '/phases', Phase_Library, 'phases')
subcomponents_bp = create_library_crud_blueprint('subcomponents', '/subcomponents', Subcomponent_Library, 'subcomponents')


