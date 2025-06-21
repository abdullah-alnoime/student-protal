CREATE DATABASE IF NOT EXISTS student_portal;
USE student_portal;

CREATE TABLE IF NOT EXISTS student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS enrollment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id),
    FOREIGN KEY (course_id) REFERENCES course(id)
);

-- إضافة بعض الدورات للاختبار
INSERT INTO course (title, description) VALUES 
('مقدمة في علوم الحاسوب', 'دورة تمهيدية تغطي أساسيات علوم الحاسوب والبرمجة'),
('قواعد البيانات المتقدمة', 'دورة متقدمة في تصميم وإدارة قواعد البيانات'),
('تطوير تطبيقات الويب', 'تعلم كيفية بناء تطبيقات ويب حديثة باستخدام Flask وDjango'),
('الذكاء الاصطناعي', 'مقدمة في مفاهيم وتقنيات الذكاء الاصطناعي وتعلم الآلة'),
('أمن المعلومات', 'دورة شاملة في أساسيات أمن المعلومات وحماية البيانات');
