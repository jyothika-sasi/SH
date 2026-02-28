from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    education = db.Column(db.String(200))
    skill_level = db.Column(db.String(50))
    role = db.Column(db.String(50), nullable=False)  # women, mentor, recruiter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Women specific fields
    interests = db.Column(db.String(500))
    completed_courses = db.Column(db.String(500))
    
    # Mentor specific fields
    expertise = db.Column(db.String(500))
    experience_years = db.Column(db.Integer)
    
    # Recruiter specific fields
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    
    # Relationships
    courses_teaching = db.relationship('Course', backref='mentor', lazy=True)
    jobs_posted = db.relationship('Job', backref='recruiter', lazy=True)
    mentorship_requests = db.relationship('Mentorship', foreign_keys='Mentorship.mentee_id', backref='mentee', lazy=True)
    mentorship_offered = db.relationship('Mentorship', foreign_keys='Mentorship.mentor_id', backref='mentor', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)
    certificates = db.relationship('Certificate', backref='user', lazy=True)
    applications = db.relationship('Application', backref='user', lazy=True)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    level = db.Column(db.String(50))  # beginner, intermediate, advanced
    duration = db.Column(db.String(50))
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    thumbnail = db.Column(db.String(200), default='default-course.jpg')
    price = db.Column(db.Float, default=0.0)
    
    # Relationships
    progress = db.relationship('Progress', backref='course', lazy=True)
    certificates = db.relationship('Certificate', backref='course', lazy=True)

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(200))
    location = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, shortlisted, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    resume = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)

class Mentorship(db.Model):
    __tablename__ = 'mentorships'
    
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected, completed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    session_notes = db.Column(db.Text)

class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    progress_percentage = db.Column(db.Float, default=0)
    completed = db.Column(db.Boolean, default=False)
    certificate_issued = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    certificate_number = db.Column(db.String(100), unique=True)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    download_url = db.Column(db.String(200))