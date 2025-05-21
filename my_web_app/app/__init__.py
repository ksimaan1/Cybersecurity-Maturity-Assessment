from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
bootstrap = Bootstrap5()
jwt = JWTManager()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.views.bank import bank as bank_blueprint
    app.register_blueprint(bank_blueprint, url_prefix='/bank')
    
    from app.views.supervisor import supervisor as supervisor_blueprint
    app.register_blueprint(supervisor_blueprint, url_prefix='/supervisor')
    
    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    
    # Set up language selection
    @app.before_request
    def before_request():
        # Set language from session or default
        if 'language' not in session:
            session['language'] = request.accept_languages.best_match(app.config['LANGUAGES']) or app.config['DEFAULT_LANGUAGE']
    
    return app