from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Global variable to store table names
TABLE_NAMES_CACHE = []

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
    with app.app_context():
        from .helper_functions.table_names_cache import retrieve_table_names
        global TABLE_NAMES_CACHE
        TABLE_NAMES_CACHE = retrieve_table_names()
    return app

def register_blueprints(app):
    with app.app_context():
        from .routes import auth_bp
        app.register_blueprint(auth_bp)
        
        from .routes import current_user_bp
        app.register_blueprint(current_user_bp, url_prefix='/current-user')

        from .routes import dev_tests_bp
        app.register_blueprint(dev_tests_bp, url_prefix='/dev_tests')

def register_error_handlers(app):
    with app.app_context():
        @app.errorhandler(404)
        def page_not_found(error):
            return "Oops! Page not found.", 404