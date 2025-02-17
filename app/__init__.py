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
        app.register_blueprint(current_user.bp, url_prefix='/current-user')

        from .routes import dev_tests
        app.register_blueprint(dev_tests.bp, url_prefix='/dev_tests')

        from .routes import database_manipulation
        app.register_blueprint(database_manipulation.bp, url_prefix='/database_manipulation')

        from .routes import exercises
        app.register_blueprint(exercises.bp, url_prefix='/exercises')

def initialize_database(app, db):
    with app.app_context():
        db.create_all()

        # Initialize the record of the schema.
        from .helper_functions.table_schema_cache import get_database_schema
        app.table_schema = get_database_schema(db)


def register_error_handlers(app):
    with app.app_context():
        @app.errorhandler(404)
        def page_not_found(error):
            return "Oops! Page not found.", 404
