# This file makes the routes directory a Python package
from flask import Blueprint

# Create blueprints for different route modules
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
courses_bp = Blueprint('courses', __name__)
jobs_bp = Blueprint('jobs', __name__)
mentor_bp = Blueprint('mentor', __name__)

# Import routes to register them with blueprints
from . import auth, dashboard, courses, jobs, mentor