from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255))
    profile_picture = db.Column(db.String(255), default='default-profile.jpg')
    bio = db.Column(db.Text, nullable=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    ratings = db.relationship('CourseRating', backref='student', lazy=True)
    notifications = db.relationship('Notification', backref='student', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'join_date': self.join_date.strftime('%Y-%m-%d') if self.join_date else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        }

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(255), default='default-course.jpg')
    instructor = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.String(50), nullable=True)  # e.g., "8 weeks"
    level = db.Column(db.String(20), nullable=True)  # e.g., "Beginner", "Intermediate", "Advanced"
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    ratings = db.relationship('CourseRating', backref='course', lazy=True)
    
    def average_rating(self):
        if not self.ratings or len(self.ratings) == 0:
            return 0
        return sum(r.rating for r in self.ratings) / len(self.ratings)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image': self.image,
            'instructor': self.instructor,
            'duration': self.duration,
            'level': self.level,
            'category': self.category,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
            'average_rating': self.average_rating(),
            'ratings_count': len(self.ratings)
        }

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=0)  # Progress percentage (0-100)
    completed = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'progress': self.progress,
            'completed': self.completed
        }

class CourseRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    rating = db.Column(db.Integer)  # 1-5 stars
    review = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'rating': self.rating,
            'review': self.review,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(20), default='info')  # 'info', 'success', 'warning', 'danger'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'read': self.read,
            'notification_type': self.notification_type
        }
