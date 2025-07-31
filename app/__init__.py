from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from config import Config

bcrypt = Bcrypt()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})
    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)
    initialize_database(app, db)

    return app

def register_blueprints(app):
    with app.app_context():
        from .routes import auth
        app.register_blueprint(auth.bp)

        from .routes import current_user
        app.register_blueprint(current_user.bp, url_prefix='/current_user')

        from .routes import database_manipulation
        app.register_blueprint(database_manipulation.bp, url_prefix='/database_manipulation')

        from .routes import dev_tests
        app.register_blueprint(dev_tests.bp, url_prefix='/dev_tests')

        from .routes import libraries as library_routes
        app.register_blueprint(library_routes.equipment_bp, url_prefix='/equipment')
        app.register_blueprint(library_routes.general_exercises_bp, url_prefix='/general_exercises')
        app.register_blueprint(library_routes.exercises_bp, url_prefix='/exercises')
        app.register_blueprint(library_routes.goals_bp, url_prefix='/goals')
        app.register_blueprint(library_routes.phases_bp, url_prefix='/phases')
        app.register_blueprint(library_routes.loading_systems_bp, url_prefix='/loading_systems')
        app.register_blueprint(library_routes.phase_components_bp, url_prefix='/phase_components')
        app.register_blueprint(library_routes.components_bp, url_prefix='/components')
        app.register_blueprint(library_routes.subcomponents_bp, url_prefix='/subcomponents')

        from .user_weekdays_availability import routes
        app.register_blueprint(routes.bp, url_prefix='/user_weekday_availability')

        from .user_macrocycles import routes
        app.register_blueprint(routes.bp, url_prefix='/user_macrocycles')

        from .user_mesocycles import routes
        app.register_blueprint(routes.bp, url_prefix='/user_mesocycles')

        from .user_microcycles import routes
        app.register_blueprint(routes.bp, url_prefix='/user_microcycles')

        from .user_workout_days import routes
        app.register_blueprint(routes.bp, url_prefix='/user_workout_days')

        from .user_workout_exercises import routes
        app.register_blueprint(routes.bp, url_prefix='/user_workout_exercises')

        from .user_exercises import routes
        app.register_blueprint(routes.bp, url_prefix='/user_exercises')
        
        from .routes import user_equipment
        app.register_blueprint(user_equipment.bp, url_prefix='/user_equipment')

        from .routes import main_agent
        app.register_blueprint(main_agent.bp, url_prefix='/main_agent')


def initialize_database(app, db):
    with app.app_context():
        db.create_all()

        # Initialize the record of the schema.
        from .utils.table_schema_cache import get_database_schema
        app.table_schema = get_database_schema(db)


def register_error_handlers(app):
    with app.app_context():
        from .error_handling import error_handler
        app.register_error_handler(404, error_handler.not_found_error)
        app.register_error_handler(400, error_handler.empty_form_error)
        app.register_error_handler(401, error_handler.unauthorized_error)
