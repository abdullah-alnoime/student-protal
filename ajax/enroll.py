from flask import Blueprint, jsonify, request, session
from models import db, Course, Enrollment, Notification, CourseRating # Assuming models.py is in the parent directory
from functools import wraps
from datetime import datetime

ajax_bp = Blueprint('ajax_bp', __name__, url_prefix='/ajax')

# Decorator for login required, similar to the one in app.py
def ajax_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@ajax_bp.route('/enroll', methods=['POST'])
@ajax_login_required
def ajax_enroll():
    data = request.json
    course_id = data.get('course_id')
    student_id = session.get('user_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'معرف الدورة مطلوب'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'الدورة غير موجودة'}), 404
    
    existing_enrollment = Enrollment.query.filter_by(
        student_id=student_id, course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({'success': False, 'message': 'أنت مسجل بالفعل في هذه الدورة'}), 400
    
    new_enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.session.add(new_enrollment)
    
    enrollment_notification = Notification(
        student_id=student_id,
        title=f'تم التسجيل في دورة جديدة',
        message=f'لقد قمت بالتسجيل في دورة "{course.title}" بنجاح. يمكنك الآن البدء في التعلم.',
        notification_type='success'
    )
    db.session.add(enrollment_notification)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'تم التسجيل في الدورة بنجاح',
        'enrollment': new_enrollment.to_dict() # Assuming Enrollment has a to_dict method
    })

@ajax_bp.route('/rate', methods=['POST'])
@ajax_login_required
def ajax_rate():
    data = request.json
    course_id = data.get('course_id')
    rating_value = data.get('rating') # Renamed to avoid conflict with the model name
    review = data.get('review')
    student_id = session.get('user_id')

    if not course_id or rating_value is None:
        return jsonify({'success': False, 'message': 'معرف الدورة والتقييم مطلوبان'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'الدورة غير موجودة'}), 404

    enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not enrollment:
        return jsonify({'success': False, 'message': 'يجب أن تكون مسجلاً في الدورة لتقييمها'}), 400

    existing_rating = CourseRating.query.filter_by(student_id=student_id, course_id=course_id).first()

    if existing_rating:
        existing_rating.rating = rating_value
        existing_rating.review = review
        existing_rating.timestamp = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'تم تحديث تقييمك بنجاح',
            'rating': existing_rating.to_dict() # Assuming CourseRating has to_dict
        })

    new_rating = CourseRating(
        student_id=student_id, 
        course_id=course_id,
        rating=rating_value,
        review=review
    )
    db.session.add(new_rating)
    db.session.commit()

    return jsonify({
        'success': True, 
        'message': 'تم إضافة تقييمك بنجاح',
        'rating': new_rating.to_dict() # Assuming CourseRating has to_dict
    })

@ajax_bp.route('/update_progress', methods=['POST'])
@ajax_login_required
def ajax_update_progress():
    data = request.json
    course_id = data.get('course_id')
    progress = data.get('progress')
    student_id = session.get('user_id')

    if not course_id or progress is None:
        return jsonify({'success': False, 'message': 'معرف الدورة ونسبة التقدم مطلوبان'}), 400

    enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not enrollment:
        return jsonify({'success': False, 'message': 'أنت غير مسجل في هذه الدورة'}), 404

    enrollment.progress = progress
    if progress == 100:
        enrollment.completed = True
        course = Course.query.get(course_id)
        completion_notification = Notification(
            student_id=student_id,
            title='تهانينا! لقد أكملت دورة',
            message=f'لقد أكملت دورة "{course.title}" بنجاح. استمر في التعلم واستكشاف المزيد من الدورات.',
            notification_type='success'
        )
        db.session.add(completion_notification)

    db.session.commit()

    return jsonify({
        'success': True, 
        'message': 'تم تحديث التقدم بنجاح',
        'progress': progress,
        'completed': enrollment.completed
    })