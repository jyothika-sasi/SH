from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///she_empowerment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# ── DATABASE MODELS ──────────────────────────────────────────────────────────

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

    # ── RELATIONSHIPS (needed so templates can do app.user, req.mentee, m.mentee) ──
    applications = db.relationship('Application', foreign_keys='Application.user_id',
                                   backref='user', lazy=True)
    mentee_requests = db.relationship('Mentorship', foreign_keys='Mentorship.mentee_id',
                                      backref='mentee', lazy=True)
    mentor_requests = db.relationship('Mentorship', foreign_keys='Mentorship.mentor_id',
                                      backref='mentor_rel', lazy=True)
    progress_records = db.relationship('Progress', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    level = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship('Progress', backref='course', lazy=True)


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

    applications = db.relationship('Application', backref='job', lazy=True)
    recruiter = db.relationship('User', foreign_keys=[recruiter_id])


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    # .user backref comes from User.applications
    # .job  backref comes from Job.applications


class Mentorship(db.Model):
    __tablename__ = 'mentorships'

    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    # .mentee backref comes from User.mentee_requests (foreign_keys=mentee_id)


class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    progress_percentage = db.Column(db.Float, default=0)
    completed = db.Column(db.Boolean, default=False)
    certificate_issued = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    # .course  backref comes from Course.enrollments
    # .student backref comes from User.progress_records


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful! 🌸', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name             = request.form.get('name', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone            = request.form.get('phone', '').strip()
        location         = request.form.get('location', '').strip()
        role             = request.form.get('role', 'women')

        if not all([name, email, password, confirm_password, phone, location]):
            flash('Please fill in all fields', 'error')
            return render_template('signup.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return render_template('signup.html')

        new_user = User(name=name, email=email, phone=phone,
                        location=location, role=role)
        new_user.set_password(password)

        if role == 'mentor':
            new_user.expertise = request.form.get('expertise', '')
            exp = request.form.get('experience_years', '0')
            new_user.experience_years = int(exp) if exp.isdigit() else 0
        elif role == 'recruiter':
            new_user.company = request.form.get('company', '')
            new_user.position = request.form.get('position', '')

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login. 🌸', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return render_template('signup.html')

    return render_template('signup.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Password reset instructions sent to your email 💕', 'success')
        else:
            flash('If this email is registered, you will receive reset instructions', 'info')

        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'women':
        courses  = Course.query.limit(3).all()
        jobs     = Job.query.filter_by(is_active=True).limit(3).all()
        mentors  = User.query.filter_by(role='mentor').limit(3).all()
        progress = Progress.query.filter_by(user_id=current_user.id).all()
        return render_template('women_dashboard.html',
                               courses=courses, jobs=jobs,
                               mentors=mentors, progress=progress)

    elif current_user.role == 'mentor':
        mentees = Mentorship.query.filter_by(
            mentor_id=current_user.id, status='accepted').all()
        pending_requests = Mentorship.query.filter_by(
            mentor_id=current_user.id, status='pending').count()
        return render_template('mentor_dashboard.html',
                               mentees=mentees,
                               pending_requests=pending_requests)

    elif current_user.role == 'recruiter':
        jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
        applications = Application.query.join(Job).filter(
            Job.recruiter_id == current_user.id).count()
        return render_template('recruiter_dashboard.html',
                               jobs=jobs, applications=applications)

    return redirect(url_for('index'))


# ── WOMEN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/skill-assessment', methods=['GET', 'POST'])
@login_required
def skill_assessment():
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        current_user.education   = request.form.get('education', '')
        current_user.interests   = request.form.get('interest', '')
        current_user.skill_level = request.form.get('computer_skills', '')
        db.session.commit()
        flash('Skill assessment completed! 🌸', 'success')
        return redirect(url_for('dashboard'))
    return render_template('skill_assessment.html')


@app.route('/courses')
@login_required
def courses():
    all_courses = Course.query.all()
    return render_template('courses.html', courses=all_courses)


@app.route('/my-courses')
@login_required
def my_courses():
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    enrollments = Progress.query.filter_by(user_id=current_user.id).all()
    return render_template('my_courses.html', enrollments=enrollments)


@app.route('/enroll-course/<int:course_id>')
@login_required
def enroll_course(course_id):
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    course = Course.query.get_or_404(course_id)

    existing = Progress.query.filter_by(
        user_id=current_user.id, course_id=course_id).first()
    if existing:
        flash(f'Already enrolled in {course.title}', 'info')
        return redirect(url_for('courses'))

    progress = Progress(user_id=current_user.id, course_id=course_id)
    db.session.add(progress)
    db.session.commit()
    flash(f'Successfully enrolled in {course.title}! 🌸', 'success')
    return redirect(url_for('dashboard'))


@app.route('/mentors')
@login_required
def mentors():
    all_mentors = User.query.filter_by(role='mentor').all()
    return render_template('mentors.html', mentors=all_mentors)


@app.route('/request-mentor/<int:mentor_id>')
@login_required
def request_mentor(mentor_id):
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    existing = Mentorship.query.filter_by(
        mentee_id=current_user.id, mentor_id=mentor_id).first()
    if existing:
        flash('You already requested this mentor', 'info')
        return redirect(url_for('mentors'))

    mentorship = Mentorship(mentee_id=current_user.id, mentor_id=mentor_id)
    db.session.add(mentorship)
    db.session.commit()
    flash('Mentorship request sent! 💕', 'success')
    return redirect(url_for('dashboard'))


@app.route('/apply-job/<int:job_id>')
@login_required
def apply_job(job_id):
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    job = Job.query.get_or_404(job_id)

    existing = Application.query.filter_by(
        user_id=current_user.id, job_id=job_id).first()
    if existing:
        flash('You already applied for this job', 'info')
        return redirect(url_for('post_job'))

    application = Application(user_id=current_user.id, job_id=job_id)
    db.session.add(application)
    db.session.commit()
    flash(f'Applied to {job.title} successfully! 🌸', 'success')
    return redirect(url_for('dashboard'))


# ── MENTOR ROUTES ─────────────────────────────────────────────────────────────

@app.route('/mentorship-requests')
@login_required
def mentorship_requests():
    if current_user.role != 'mentor':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    reqs = Mentorship.query.filter_by(
        mentor_id=current_user.id, status='pending').all()
    return render_template('mentorship_requests.html', requests=reqs)


@app.route('/accept-mentor/<int:request_id>')
@login_required
def accept_mentor(request_id):
    mentorship = Mentorship.query.get_or_404(request_id)
    if mentorship.mentor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    mentorship.status = 'accepted'
    db.session.commit()
    flash('Mentorship request accepted! 💕', 'success')
    return redirect(url_for('mentorship_requests'))


@app.route('/reject-mentor/<int:request_id>')
@login_required
def reject_mentor(request_id):
    mentorship = Mentorship.query.get_or_404(request_id)
    if mentorship.mentor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    mentorship.status = 'rejected'
    db.session.commit()
    flash('Request declined', 'info')
    return redirect(url_for('mentorship_requests'))


# ── RECRUITER ROUTES ──────────────────────────────────────────────────────────

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title        = request.form.get('title', '').strip()
        description  = request.form.get('description', '').strip()
        location     = request.form.get('location', '').strip()
        requirements = request.form.get('requirements', '').strip()
        salary_range = request.form.get('salary_range', '').strip()

        if not all([title, description, location]):
            flash('Please fill in all required fields', 'error')
            return render_template('post_job.html')

        job = Job(
            title=title,
            description=description,
            company=current_user.company or '',
            location=location,
            requirements=requirements,
            salary_range=salary_range,
            recruiter_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully! 💼', 'success')
        return redirect(url_for('dashboard'))

    return render_template('post_job.html')


@app.route('/view-applicants/<int:job_id>')
@login_required
def view_applicants(job_id):
    if current_user.role != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    job = Job.query.get_or_404(job_id)
    if job.recruiter_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('view_applicants.html', job=job,
                           applications=applications)


@app.route('/update-application/<int:app_id>/<string:status>')
@login_required
def update_application(app_id, status):
    application = Application.query.get_or_404(app_id)
    job = Job.query.get(application.job_id)

    if job.recruiter_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    application.status = status
    db.session.commit()
    flash(f'Application marked as {status} ✓', 'success')
    return redirect(url_for('view_applicants', job_id=job.id))


# ── LOGOUT ────────────────────────────────────────────────────────────────────

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out. See you soon! 🌸', 'info')
    return redirect(url_for('index'))


# ── DB INIT ───────────────────────────────────────────────────────────────────

@app.cli.command("init-db")
def init_db():
    db.create_all()

    sample_courses = [
        Course(title="Web Development Fundamentals",
               description="Learn HTML, CSS, and JavaScript from scratch",
               category="Technology", level="Beginner", duration="8 weeks"),
        Course(title="Digital Marketing Basics",
               description="Master social media, SEO and digital strategy",
               category="Marketing", level="Beginner", duration="6 weeks"),
        Course(title="Data Analysis with Python",
               description="Learn data manipulation and visualization",
               category="Technology", level="Intermediate", duration="10 weeks"),
        Course(title="Leadership & Communication",
               description="Build confidence and leadership skills",
               category="Personal Development", level="Beginner", duration="4 weeks"),
        Course(title="Graphic Design Fundamentals",
               description="Learn Canva, Figma and design principles",
               category="Design", level="Beginner", duration="6 weeks"),
    ]

    for course in sample_courses:
        if not Course.query.filter_by(title=course.title).first():
            db.session.add(course)

    db.session.commit()
    print("✓ Database initialized!")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)