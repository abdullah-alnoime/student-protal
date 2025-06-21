from flask import Blueprint, jsonify, request, session
from models import Course, Notification, db # Assuming models.py is in the parent directory
from functools import wraps

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

# Decorator for login required, similar to the one in app.py but for API
# This is a simplified version for API, real app might need more robust auth (e.g., tokens)
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/courses')
def api_courses():
    category = request.args.get('category')
    level = request.args.get('level')
    search = request.args.get('search')
    
    query = Course.query
    
    if category:
        query = query.filter(Course.category == category)
    if level:
        query = query.filter(Course.level == level)
    if search:
        query = query.filter(Course.title.like(f'%{search}%') | Course.description.like(f'%{search}%'))
    
    courses = query.all()
    courses_data = [course.to_dict() for course in courses]
    return jsonify(courses_data)

@api_bp.route('/notifications/unread')
@api_login_required # Protecting this API endpoint
def api_unread_notifications():
    student_id = session.get('user_id')
    notifications = Notification.query.filter_by(student_id=student_id, read=False).order_by(Notification.timestamp.desc()).all()
    return jsonify([n.to_dict() for n in notifications])