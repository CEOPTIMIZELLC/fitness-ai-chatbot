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
        app.register_blueprint(library_routes.exercises_bp, url_prefix='/exercises')
        app.register_blueprint(library_routes.goals_bp, url_prefix='/goals')
        app.register_blueprint(library_routes.phases_bp, url_prefix='/phases')
        app.register_blueprint(library_routes.loading_systems_bp, url_prefix='/loading_systems')
        app.register_blueprint(library_routes.phase_components_bp, url_prefix='/phase_components')
        app.register_blueprint(library_routes.components_bp, url_prefix='/components')
        app.register_blueprint(library_routes.subcomponents_bp, url_prefix='/subcomponents')

        from .routes import user_weekday_availability
        app.register_blueprint(user_weekday_availability.bp, url_prefix='/user_weekday_availability')

        from .routes import user_macrocycles
        app.register_blueprint(user_macrocycles.bp, url_prefix='/user_macrocycles')

        from .routes import user_mesocycles
        app.register_blueprint(user_mesocycles.bp, url_prefix='/user_mesocycles')

        from .routes import user_microcycles
        app.register_blueprint(user_microcycles.bp, url_prefix='/user_microcycles')

        from .routes import user_workout_days
        app.register_blueprint(user_workout_days.bp, url_prefix='/user_workout_days')

        from .routes import user_workout_exercises
        app.register_blueprint(user_workout_exercises.bp, url_prefix='/user_workout_exercises')

        from .routes import user_exercises
        app.register_blueprint(user_exercises.bp, url_prefix='/user_exercises')
        
        from .routes import user_equipment
        app.register_blueprint(user_equipment.bp, url_prefix='/user_equipment')

def initialize_database(app, db):
    with app.app_context():
        db.create_all()

        # Initialize the record of the schema.
        from .utils.table_schema_cache import get_database_schema
        app.table_schema = get_database_schema(db)


def register_error_handlers(app):
    with app.app_context():
        @app.errorhandler(404)
        def page_not_found(error):
            return "Oops! Page not found.", 404
