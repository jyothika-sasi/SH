from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Course, Progress, Certificate, db
from . import courses_bp
from datetime import datetime
import uuid

@courses_bp.route('/courses')
@login_required
def list_courses():
    category = request.args.get('category', 'all')
    level = request.args.get('level', 'all')
    
    query = Course.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    if level != 'all':
        query = query.filter_by(level=level)
    
    courses = query.all()
    return render_template('courses.html', courses=courses)

@courses_bp.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    return render_template('course_detail.html', course=course, progress=progress)

@courses_bp.route('/enroll-course/<int:course_id>')
@login_required
def enroll_course(course_id):
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing:
        flash('You are already enrolled in this course', 'info')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    
    progress = Progress(user_id=current_user.id, course_id=course_id)
    db.session.add(progress)
    db.session.commit()
    flash(f'Successfully enrolled in {course.title}', 'success')
    return redirect(url_for('courses.course_detail', course_id=course_id))

@courses_bp.route('/update-progress/<int:course_id>', methods=['POST'])
@login_required
def update_progress(course_id):
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    progress = Progress.query.filter_by(user_id=current_user.id, course_id=course_id).first_or_404()
    percentage = float(request.form.get('percentage', 0))
    
    progress.progress_percentage = percentage
    if percentage >= 100:
        progress.completed = True
        progress.completed_at = datetime.utcnow()
        
        # Generate certificate if not already issued
        if not progress.certificate_issued:
            certificate = Certificate(
                user_id=current_user.id,
                course_id=course_id,
                certificate_number=f"CERT-{uuid.uuid4().hex[:8].upper()}"
            )
            db.session.add(certificate)
            progress.certificate_issued = True
            flash('Congratulations! You have completed the course. Your certificate is ready.', 'success')
    
    progress.last_accessed = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('courses.course_detail', course_id=course_id))

@courses_bp.route('/my-courses')
@login_required
def my_courses():
    if current_user.role != 'women':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.index'))
    
    enrollments = Progress.query.filter_by(user_id=current_user.id).all()
    return render_template('my_courses.html', enrollments=enrollments)