"""
Flask application factory for Sistema de Chamada SUS.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS

from config import config

db = SQLAlchemy()
socketio = SocketIO()


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Use threading for testing, gevent for production
    async_mode = 'threading' if config_name == 'testing' else 'gevent'
    socketio.init_app(app, cors_allowed_origins="*", async_mode=async_mode)
    CORS(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
