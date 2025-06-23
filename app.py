from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Student, Course, Enrollment, CourseRating, Notification
from forms import RegistrationForm, LoginForm # Added import for Flask-WTF forms
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# Import Blueprints
from api import api_bp  # Assuming api_bp is defined in api/__init__.py
from ajax.enroll import ajax_bp # Assuming ajax_bp is defined in ajax/enroll.py

app.register_blueprint(api_bp)
app.register_blueprint(ajax_bp)
app.config['SECRET_KEY'] = os.urandom(24)
# TODO: Replace with your MySQL connection string
# Example: app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@host/dbname'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://uossi9vngk1oimlt:3h2StFWlMaDzpYFYV40O@biwhz4mugpsww65lpmd1-mysql.services.clever-cloud.com:3306/biwhz4mugpsww65lpmd1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True  # للإنتاج فقط، استخدم False للتطوير المحلي
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# تفعيل حماية CSRF
csrf = CSRFProtect(app)
db.init_app(app)

# دالة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('login'))
        
        # تحديث وقت آخر نشاط
        session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        return f(*args, **kwargs)
    return decorated_function

# دالة للتحقق من وقت النشاط وتسجيل الخروج التلقائي
@app.before_request
def check_session_timeout():
    if 'user_id' in session and 'last_activity' in session:
        last_activity = datetime.strptime(session['last_activity'], '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() - last_activity > timedelta(minutes=30):  # تسجيل الخروج بعد 30 دقيقة من عدم النشاط
            session.clear()
            flash('تم تسجيل خروجك تلقائياً بسبب عدم النشاط', 'warning')
            return redirect(url_for('login'))

# الصفحة الرئيسية
@app.route('/')
def index():
    # الحصول على الدورات الأكثر شعبية (أعلى تقييم)
    popular_courses = Course.query.order_by(Course.id.desc()).limit(3).all()
    return render_template('index.html', popular_courses=popular_courses)

# صفحة التسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_student = Student(name=form.full_name.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(new_student)
        db.session.commit()

        # إنشاء إشعار ترحيبي
        welcome_notification = Notification(
            student_id=new_student.id,
            title='مرحباً بك في بوابة الطلاب!',
            message='نرحب بك في منصتنا التعليمية. استكشف الدورات المتاحة وابدأ رحلتك التعليمية الآن.',
            notification_type='success'
        )
        db.session.add(welcome_notification)
        db.session.commit()

        flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
    elif request.method == 'POST': # If form validation fails but it's a POST request, show errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return render_template('register.html', form=form)

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()
        if student and check_password_hash(student.password_hash, form.password.data):
            session['user_id'] = student.id
            session['user_name'] = student.name
            session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if form.remember.data:
                session.permanent = True
            
            # تحديث وقت آخر تسجيل دخول (if last_login attribute exists)
            if hasattr(student, 'last_login'):
                student.last_login = datetime.utcnow()
                db.session.commit()

            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('فشل تسجيل الدخول. يرجى التحقق من البريد الإلكتروني وكلمة المرور.', 'danger')
    elif request.method == 'POST': # If form validation fails but it's a POST request, show errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return render_template('login.html', form=form)

# لوحة التحكم
@app.route('/dashboard')
@login_required
def dashboard():
    student_id = session.get('user_id')
    student = Student.query.get(student_id)
    
    # الحصول على الدورات المسجل فيها
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    enrolled_courses = []
    
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            enrolled_courses.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'image': course.image,
                'instructor': course.instructor,
                'level': course.level,
                'enrollment_date': enrollment.timestamp.strftime('%Y-%m-%d'),
                'progress': enrollment.progress,
                'completed': enrollment.completed
            })
    
    # الحصول على الإشعارات غير المقروءة
    unread_notifications = Notification.query.filter_by(student_id=student_id, read=False).order_by(Notification.timestamp.desc()).all()
    
    # إحصائيات الطالب
    stats = {
        'total_courses': len(enrolled_courses),
        'completed_courses': sum(1 for course in enrolled_courses if course['completed']),
        'avg_progress': sum(course['progress'] for course in enrolled_courses) / len(enrolled_courses) if enrolled_courses else 0,
        'join_date': student.join_date.strftime('%Y-%m-%d') if student.join_date else None
    }
    
    return render_template('dashboard.html', 
                          student=student, 
                          enrolled_courses=enrolled_courses, 
                          notifications=unread_notifications,
                          stats=stats)

# صفحة الدورات
@app.route('/courses')
@login_required
def courses():
    # الحصول على الفئات للتصفية
    categories = db.session.query(Course.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    # الحصول على المستويات للتصفية
    levels = db.session.query(Course.level).distinct().all()
    levels = [l[0] for l in levels if l[0]]
    
    return render_template('courses.html', categories=categories, levels=levels)

# صفحة تفاصيل الدورة
@app.route('/course/<int:course_id>')
@login_required
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    student_id = session.get('user_id')
    
    # التحقق مما إذا كان الطالب مسجلاً في الدورة
    enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    
    # الحصول على تقييمات الدورة
    ratings = CourseRating.query.filter_by(course_id=course_id).order_by(CourseRating.timestamp.desc()).all()
    
    # التحقق مما إذا كان الطالب قد قيّم الدورة
    user_rating = CourseRating.query.filter_by(student_id=student_id, course_id=course_id).first()
    
    return render_template('course_details.html', 
                          course=course, 
                          enrollment=enrollment, 
                          ratings=ratings, 
                          user_rating=user_rating)

# صفحة الملف الشخصي
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    student_id = session.get('user_id')
    student = Student.query.get(student_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        bio = request.form.get('bio')
        
        if name:
            student.name = name
            session['user_name'] = name
        
        student.bio = bio
        
        # معالجة تحميل الصورة الشخصية
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # حفظ الصورة وتحديث مسار الصورة في قاعدة البيانات
                filename = f"profile_{student_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
                file.save(os.path.join(app.static_folder, 'uploads', filename))
                student.profile_picture = filename
        
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', student=student)

# صفحة الإشعارات
@app.route('/notifications')
@login_required
def notifications():
    student_id = session.get('user_id')
    
    # الحصول على جميع الإشعارات
    all_notifications = Notification.query.filter_by(student_id=student_id).order_by(Notification.timestamp.desc()).all()
    
    # تحديث حالة الإشعارات غير المقروءة
    unread_notifications = Notification.query.filter_by(student_id=student_id, read=False).all()
    for notification in unread_notifications:
        notification.read = True
    
    db.session.commit()
    
    return render_template('notifications.html', notifications=all_notifications)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# API and AJAX routes are now in Blueprints (api/__init__.py and ajax/enroll.py)

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from urllib.parse import urlparse, urlunparse

# إنشاء قاعدة البيانات
@app.before_first_request
def create_tables():
    try:
        # Attempt to create all tables directly
        db.create_all()
    except OperationalError as e:
        # Check if the error is due to the database not existing (MySQL error code 1049)
        if e.orig and e.orig.args[0] == 1049: # MySQL ER_BAD_DB_ERROR
            app.logger.info("Database does not exist. Attempting to create it.")
            
            # Parse the original URI to get components
            original_uri = app.config['SQLALCHEMY_DATABASE_URI']
            parsed_uri = urlparse(original_uri)
            db_name = parsed_uri.path.lstrip('/')
            
            # Create a new URI without the database name
            # This connects to the MySQL server itself
            server_uri_parts = parsed_uri._replace(path='')
            server_uri = urlunparse(server_uri_parts)
            
            try:
                # Create an engine to connect to the MySQL server (not a specific database)
                engine = create_engine(server_uri)
                with engine.connect() as connection:
                    connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
                    connection.commit()
                app.logger.info(f"Database '{db_name}' created successfully or already exists.")
                
                # Now that the database exists, try creating tables again
                # The original db object is already configured with the full URI including the database name
                db.create_all()
                app.logger.info("Tables created successfully.")
            except Exception as create_db_e:
                app.logger.error(f"Could not create database '{db_name}': {create_db_e}")
                raise # Re-raise the exception if database creation fails
        else:
            # If the error is not about a non-existent database, re-raise it
            app.logger.error(f"An OperationalError occurred: {e}")
            raise
    except Exception as ex:
        app.logger.error(f"An unexpected error occurred during initial setup: {ex}")
        raise
    
    # The rest of the original create_tables function remains the same
    
    # إنشاء مجلد التحميلات إذا لم يكن موجوداً
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # إضافة بعض الدورات للاختبار إذا لم تكن موجودة
    if Course.query.count() == 0:
        courses = [
            Course(
                title='مقدمة في علوم الحاسوب', 
                description='دورة تمهيدية تغطي أساسيات علوم الحاسوب والبرمجة',
                instructor='د. أحمد محمد',
                duration='8 أسابيع',
                level='مبتدئ',
                category='علوم الحاسوب'
            ),
            Course(
                title='قواعد البيانات المتقدمة', 
                description='دورة متقدمة في تصميم وإدارة قواعد البيانات',
                instructor='د. سارة أحمد',
                duration='10 أسابيع',
                level='متقدم',
                category='قواعد البيانات'
            ),
            Course(
                title='تطوير تطبيقات الويب', 
                description='تعلم كيفية بناء تطبيقات ويب حديثة باستخدام Flask وDjango',
                instructor='م. محمد علي',
                duration='12 أسبوع',
                level='متوسط',
                category='تطوير الويب'
            ),
            Course(
                title='الذكاء الاصطناعي', 
                description='مقدمة في مفاهيم وتقنيات الذكاء الاصطناعي وتعلم الآلة',
                instructor='د. ليلى حسن',
                duration='14 أسبوع',
                level='متقدم',
                category='الذكاء الاصطناعي'
            ),
            Course(
                title='أمن المعلومات', 
                description='دورة شاملة في أساسيات أمن المعلومات وحماية البيانات',
                instructor='د. خالد عمر',
                duration='8 أسابيع',
                level='متوسط',
                category='أمن المعلومات'
            ),
            Course(
                title='تطوير تطبيقات الهاتف المحمول', 
                description='تعلم كيفية بناء تطبيقات للهواتف الذكية باستخدام React Native وFlutter',
                instructor='م. نورا سامي',
                duration='10 أسابيع',
                level='متوسط',
                category='تطوير التطبيقات'
            ),
            Course(
                title='الشبكات وأنظمة التشغيل', 
                description='دورة شاملة في أساسيات الشبكات وأنظمة التشغيل',
                instructor='د. سمير فؤاد',
                duration='12 أسبوع',
                level='مبتدئ',
                category='الشبكات'
            ),
            Course(
                title='تحليل البيانات وعلم البيانات', 
                description='تعلم كيفية تحليل البيانات واستخراج الرؤى منها باستخدام Python وR',
                instructor='د. هدى كمال',
                duration='14 أسبوع',
                level='متوسط',
                category='علم البيانات'
            )
        ]
        
        for course in courses:
            db.session.add(course)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
