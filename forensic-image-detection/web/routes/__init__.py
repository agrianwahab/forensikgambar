"""
Routes initialization for Forensic Image Detection System
"""

from flask import Blueprint

# Initialize blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)
auth_bp = Blueprint('auth', __name__)

# Import routes to register them with blueprints
from . import main, api, auth
