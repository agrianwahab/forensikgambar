"""
Web application module initialization for Forensic Image Detection System
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config=None):
    """
    Application factory function to create and configure the Flask app
    """
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_for_development_super_secret'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///forensic_webapp.db'), # Nama DB diubah
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, '../uploads'), # Folder untuk upload gambar asli
        RESULTS_FOLDER=os.path.join(app.root_path, '../results_sistem_deteksi'), # Folder untuk hasil dari sistem_deteksi
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload
        ALLOWED_EXTENSIONS={'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp'} # Sesuai config.py sistem_deteksi
    )
    
    # Override with provided config if any
    if config:
        app.config.update(config)
    
    # Ensure upload and results directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Nama blueprint.nama_fungsi
    login_manager.login_message_category = 'info'
    socketio.init_app(app, cors_allowed_origins="*") # Izinkan semua origin untuk SocketIO (sesuaikan di production)
    
    # Register blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Import models here to avoid circular imports if models use db
    from . import models 

    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created (if not exist). DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    # Import WebSocket handlers to register them
    from . import websocket

    return app
