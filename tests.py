import unittest
from app import app, db
from models import Student, Course, Enrollment, CourseRating, Notification
import json
from datetime import datetime

class StudentPortalTestCase(unittest.TestCase):
    def setUp(self):
        # Configure test database
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        
        self.app = app.test_client()
        
        # Create database tables
        with app.app_context():
            db.create_all()
            
            # Create test data
            test_student = Student(name='Test User', email='test@example.com')
            test_student.set_password('password123')
            
            test_course = Course(
                title='Test Course',
                description='This is a test course',
                instructor='Test Instructor',
                duration='8 weeks',
                level='Beginner',
                category='Testing'
            )
            
            db.session.add(test_student)
            db.session.add(test_course)
            db.session.commit()
    
    def tearDown(self):
        # Clean up database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Portal', response.data)
    
    def test_register_page(self):
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
    
    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_registration(self):
        response = self.app.post('/register', data={
            'name': 'New User',
            'email': 'new@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check if user was created
        with app.app_context():
            user = Student.query.filter_by(email='new@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'New User')
    
    def test_login(self):
        # First login to get session
        response = self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
    
    def test_invalid_login(self):
        response = self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_dashboard_requires_login(self):
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in', response.data)
    
    def test_courses_api(self):
        response = self.app.get('/api/courses')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        
        # Check if test course is in the response
        if data:
            self.assertEqual(data[0]['title'], 'Test Course')
    
    def test_enroll_in_course(self):
        # First login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Get course ID
        with app.app_context():
            course = Course.query.filter_by(title='Test Course').first()
            course_id = course.id
        
        # Enroll in course
        response = self.app.post('/ajax/enroll', 
                                json={'course_id': course_id},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Check if enrollment was created
        with app.app_context():
            student = Student.query.filter_by(email='test@example.com').first()
            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                course_id=course_id
            ).first()
            
            self.assertIsNotNone(enrollment)
    
    def test_rate_course(self):
        # First login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Get course ID and student ID
        with app.app_context():
            course = Course.query.filter_by(title='Test Course').first()
            course_id = course.id
            
            student = Student.query.filter_by(email='test@example.com').first()
            student_id = student.id
            
            # Create enrollment (required to rate a course)
            enrollment = Enrollment(student_id=student_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()
        
        # Rate the course
        response = self.app.post('/ajax/rate', 
                                json={
                                    'course_id': course_id,
                                    'rating': 5,
                                    'review': 'Great course!'
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Check if rating was created
        with app.app_context():
            rating = CourseRating.query.filter_by(
                student_id=student_id,
                course_id=course_id
            ).first()
            
            self.assertIsNotNone(rating)
            self.assertEqual(rating.rating, 5)
            self.assertEqual(rating.review, 'Great course!')
    
    def test_update_progress(self):
        # First login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Get course ID and student ID
        with app.app_context():
            course = Course.query.filter_by(title='Test Course').first()
            course_id = course.id
            
            student = Student.query.filter_by(email='test@example.com').first()
            student_id = student.id
            
            # Create enrollment
            enrollment = Enrollment(student_id=student_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()
        
        # Update progress
        response = self.app.post('/ajax/update_progress', 
                                json={
                                    'course_id': course_id,
                                    'progress': 75
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Check if progress was updated
        with app.app_context():
            enrollment = Enrollment.query.filter_by(
                student_id=student_id,
                course_id=course_id
            ).first()
            
            self.assertEqual(enrollment.progress, 75)
            self.assertFalse(enrollment.completed)
    
    def test_complete_course(self):
        # First login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Get course ID and student ID
        with app.app_context():
            course = Course.query.filter_by(title='Test Course').first()
            course_id = course.id
            
            student = Student.query.filter_by(email='test@example.com').first()
            student_id = student.id
            
            # Create enrollment
            enrollment = Enrollment(student_id=student_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()
        
        # Update progress to 100%
        response = self.app.post('/ajax/update_progress', 
                                json={
                                    'course_id': course_id,
                                    'progress': 100
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check if course is marked as completed
        with app.app_context():
            enrollment = Enrollment.query.filter_by(
                student_id=student_id,
                course_id=course_id
            ).first()
            
            self.assertEqual(enrollment.progress, 100)
            self.assertTrue(enrollment.completed)
            
            # Check if completion notification was created
            notification = Notification.query.filter_by(
                student_id=student_id,
                notification_type='success'
            ).first()
            
            self.assertIsNotNone(notification)
            self.assertIn('completed', notification.message.lower())

if __name__ == '__main__':
    unittest.main()
